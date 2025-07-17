"""
OCR 서비스 모듈
EasyOCR을 활용하여 건축 측량 이미지에서 텍스트와 측정값을 추출합니다.
"""

import easyocr
import cv2
import numpy as np
from PIL import Image
import re
import json
from typing import List, Dict, Tuple, Optional, Union
import logging
from pathlib import Path
import time

# 로깅 설정
logger = logging.getLogger(__name__)

class OCRService:
    """OCR 처리를 담당하는 서비스 클래스"""
    
    def __init__(self, languages: List[str] = ['en'], gpu: bool = False):
        """
        OCR 서비스 초기화
        
        Args:
            languages: 인식할 언어 목록 (기본: 영어)
            gpu: GPU 사용 여부 (기본: False, CPU 사용)
        """
        self.languages = languages
        self.gpu = gpu
        self.reader = None
        self._init_reader()
    
    def _init_reader(self):
        """EasyOCR 리더 초기화"""
        try:
            logger.info(f"EasyOCR 초기화 시작... (언어: {self.languages}, GPU: {self.gpu})")
            start_time = time.time()
            
            self.reader = easyocr.Reader(
                self.languages, 
                gpu=self.gpu,
                verbose=False  # 상세 로그 비활성화
            )
            
            init_time = time.time() - start_time
            logger.info(f"EasyOCR 초기화 완료 ({init_time:.2f}초)")
            
        except Exception as e:
            logger.error(f"EasyOCR 초기화 실패: {e}")
            raise RuntimeError(f"OCR 서비스 초기화 실패: {e}")
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        이미지 전처리 (OCR 정확도 향상)
        
        Args:
            image_path: 이미지 파일 경로
            
        Returns:
            전처리된 이미지 (numpy array)
        """
        try:
            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"이미지를 로드할 수 없습니다: {image_path}")
            
            # 원본 크기 확인
            height, width = image.shape[:2]
            logger.debug(f"원본 이미지 크기: {width}x{height}")
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 이미지 크기 조정 (너무 작으면 확대)
            if width < 800 or height < 600:
                scale_factor = max(800/width, 600/height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                logger.debug(f"이미지 확대: {new_width}x{new_height} (x{scale_factor:.2f})")
            
            # 노이즈 제거
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # 대비 향상 (CLAHE - Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 선명화 (언샤프 마스킹)
            gaussian = cv2.GaussianBlur(enhanced, (0,0), 2.0)
            sharpened = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)
            
            return sharpened
            
        except Exception as e:
            logger.error(f"이미지 전처리 실패: {e}")
            # 전처리 실패 시 원본 그레이스케일 반환
            try:
                return cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            except:
                raise ValueError(f"이미지 파일을 읽을 수 없습니다: {image_path}")
    
    def extract_text_from_image(self, image_path: str, confidence_threshold: float = 0.3) -> List[Dict]:
        """
        이미지에서 텍스트 추출
        
        Args:
            image_path: 이미지 파일 경로
            confidence_threshold: 신뢰도 임계값 (기본: 0.3)
            
        Returns:
            추출된 텍스트 정보 리스트
        """
        try:
            if self.reader is None:
                raise RuntimeError("OCR 리더가 초기화되지 않았습니다.")
            
            logger.debug(f"OCR 처리 시작: {image_path}")
            start_time = time.time()
            
            # 이미지 전처리
            processed_image = self.preprocess_image(image_path)
            
            # OCR 실행
            results = self.reader.readtext(
                processed_image,
                detail=1,  # 위치 정보 포함
                paragraph=False,  # 단어별로 분리
                width_ths=0.7,  # 텍스트 병합 임계값
                height_ths=0.7
            )
            
            # 결과 정리
            extracted_data = []
            for bbox, text, confidence in results:
                if confidence >= confidence_threshold:
                    # 텍스트 정리
                    cleaned_text = self._clean_text(text)
                    if cleaned_text:  # 유효한 텍스트만 추가
                        extracted_data.append({
                            'text': cleaned_text,
                            'original_text': text,
                            'confidence': round(confidence, 3),
                            'bbox': bbox,
                            'position': self._get_position_info(bbox),
                            'area': self._calculate_bbox_area(bbox)
                        })
            
            processing_time = time.time() - start_time
            logger.info(f"OCR 완료: {len(extracted_data)}개 텍스트 ({processing_time:.2f}초)")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"OCR 처리 실패 {image_path}: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리 및 정규화"""
        if not text:
            return ""
        
        # 기본 정리
        cleaned = text.strip()
        
        # 특수 문자 정리 (측정값에 중요한 문자는 보존)
        cleaned = re.sub(r'[^\w\s\'\".-]', ' ', cleaned)
        
        # 여러 공백을 하나로
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # 너무 짧은 텍스트 제외
        if len(cleaned) < 1:
            return ""
        
        return cleaned
    
    def _get_position_info(self, bbox) -> Dict:
        """바운딩 박스에서 위치 정보 추출"""
        # bbox는 4개 점의 좌표 [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        
        left = min(x_coords)
        right = max(x_coords)
        top = min(y_coords)
        bottom = max(y_coords)
        
        return {
            'left': left,
            'right': right,
            'top': top,
            'bottom': bottom,
            'center_x': (left + right) / 2,
            'center_y': (top + bottom) / 2,
            'width': right - left,
            'height': bottom - top
        }
    
    def _calculate_bbox_area(self, bbox) -> float:
        """바운딩 박스 면적 계산"""
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)
        return width * height
    
    def extract_measurements(self, extracted_data: List[Dict]) -> List[Dict]:
        """
        추출된 텍스트에서 측정값 패턴 인식 및 추출
        
        Args:
            extracted_data: extract_text_from_image()의 결과
            
        Returns:
            측정값 정보 리스트
        """
        measurements = []
        
        # 측정값 패턴들 (우선순위 순서)
        patterns = {
            'feet_inches': r"(\d+)'\s*(\d+)\"?",           # 12' 6" 또는 12'6"
            'feet_only': r"(\d+)'(?!\d)",                  # 12' (뒤에 숫자가 없는 경우)
            'inches_only': r"(\d+)\"(?!\d)",               # 72" (뒤에 숫자가 없는 경우)
            'decimal_feet': r"(\d+\.\d+)'?",               # 12.5 또는 12.5'
            'dimensions': r"(\d+\.?\d*)\s*[xX×]\s*(\d+\.?\d*)",  # 12 x 8, 12.5 × 8.5
            'area_sqft': r"(\d+\.?\d*)\s*sq\.?\s*ft\.?",   # 100 sq ft, 100 sqft
            'area_sqin': r"(\d+\.?\d*)\s*sq\.?\s*in\.?",   # 100 sq in
            'decimal_number': r"(\d+\.\d+)",               # 12.5 (일반 소수)
            'whole_number': r"(\d+)",                      # 12 (정수)
        }
        
        for item in extracted_data:
            text = item['text']
            measurement_found = False
            
            # 패턴별로 매칭 시도 (우선순위 순서)
            for pattern_name, pattern in patterns.items():
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                
                for match in matches:
                    measurement = {
                        'original_text': item['original_text'],
                        'cleaned_text': text,
                        'pattern_type': pattern_name,
                        'raw_match': match.group(),
                        'confidence': item['confidence'],
                        'position': item['position'],
                        'bbox_area': item['area']
                    }
                    
                    # 패턴별 값 파싱
                    success = self._parse_measurement_value(measurement, match, pattern_name)
                    
                    if success:
                        measurements.append(measurement)
                        measurement_found = True
                        break  # 첫 번째 매칭된 패턴만 사용
                
                if measurement_found:
                    break  # 하나의 패턴이 매칭되면 다른 패턴은 시도하지 않음
            
            # 측정값이 아닌 일반 텍스트도 저장 (위치 정보 등에 활용)
            if not measurement_found:
                measurements.append({
                    'original_text': item['original_text'],
                    'cleaned_text': text,
                    'pattern_type': 'text',
                    'confidence': item['confidence'],
                    'position': item['position'],
                    'bbox_area': item['area']
                })
        
        # 측정값 개수 로깅
        measurement_count = len([m for m in measurements if m['pattern_type'] != 'text'])
        text_count = len([m for m in measurements if m['pattern_type'] == 'text'])
        logger.info(f"측정값 추출 완료: {measurement_count}개 측정값, {text_count}개 텍스트")
        
        return measurements
    
    def _parse_measurement_value(self, measurement: Dict, match, pattern_name: str) -> bool:
        """측정값 파싱 및 값 계산"""
        try:
            if pattern_name == 'feet_inches':
                feet, inches = match.groups()
                measurement['feet'] = int(feet)
                measurement['inches'] = int(inches)
                measurement['total_inches'] = int(feet) * 12 + int(inches)
                measurement['total_feet'] = int(feet) + int(inches) / 12
                
            elif pattern_name == 'feet_only':
                feet = match.group(1)
                measurement['feet'] = int(feet)
                measurement['total_inches'] = int(feet) * 12
                measurement['total_feet'] = int(feet)
                
            elif pattern_name == 'inches_only':
                inches = match.group(1)
                measurement['inches'] = int(inches)
                measurement['total_inches'] = int(inches)
                measurement['total_feet'] = int(inches) / 12
                
            elif pattern_name == 'decimal_feet':
                decimal_feet = float(match.group(1))
                measurement['decimal_feet'] = decimal_feet
                measurement['total_inches'] = decimal_feet * 12
                measurement['total_feet'] = decimal_feet
                
            elif pattern_name == 'dimensions':
                width, height = match.groups()
                measurement['width'] = float(width)
                measurement['height'] = float(height)
                measurement['area'] = float(width) * float(height)
                
            elif pattern_name == 'area_sqft':
                area = float(match.group(1))
                measurement['area'] = area
                measurement['unit'] = 'sq_ft'
                
            elif pattern_name == 'area_sqin':
                area = float(match.group(1))
                measurement['area'] = area
                measurement['unit'] = 'sq_in'
                
            elif pattern_name == 'decimal_number':
                value = float(match.group(1))
                measurement['decimal_value'] = value
                measurement['possible_feet'] = value
                measurement['possible_inches'] = value * 12
                
            elif pattern_name == 'whole_number':
                value = int(match.group(1))
                measurement['integer_value'] = value
                measurement['possible_feet'] = value
                measurement['possible_inches'] = value * 12
                
            return True
            
        except (ValueError, TypeError) as e:
            logger.warning(f"측정값 파싱 실패: {match.group()} - {e}")
            return False
    
    def process_multiple_images(self, image_paths: List[str], 
                              confidence_threshold: float = 0.3) -> Dict:
        """
        여러 이미지 일괄 처리
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            confidence_threshold: OCR 신뢰도 임계값
            
        Returns:
            이미지별 처리 결과 딕셔너리
        """
        results = {}
        total_images = len(image_paths)
        
        logger.info(f"일괄 OCR 처리 시작: {total_images}개 이미지")
        
        for i, image_path in enumerate(image_paths, 1):
            try:
                logger.info(f"이미지 처리 중 ({i}/{total_images}): {Path(image_path).name}")
                
                # 텍스트 추출
                extracted_data = self.extract_text_from_image(image_path, confidence_threshold)
                
                # 측정값 추출
                measurements = self.extract_measurements(extracted_data)
                
                # 결과 정리
                results[f"image_{i}"] = {
                    'file_path': str(image_path),
                    'file_name': Path(image_path).name,
                    'extracted_data': extracted_data,
                    'measurements': measurements,
                    'summary': {
                        'total_texts': len(extracted_data),
                        'measurement_count': len([m for m in measurements if m['pattern_type'] != 'text']),
                        'text_count': len([m for m in measurements if m['pattern_type'] == 'text']),
                        'avg_confidence': np.mean([item['confidence'] for item in extracted_data]) if extracted_data else 0,
                        'patterns_found': list(set(m['pattern_type'] for m in measurements if m['pattern_type'] != 'text'))
                    }
                }
                
            except Exception as e:
                logger.error(f"이미지 처리 실패 {image_path}: {e}")
                results[f"image_{i}"] = {
                    'file_path': str(image_path),
                    'file_name': Path(image_path).name if isinstance(image_path, (str, Path)) else 'unknown',
                    'error': str(e),
                    'error_type': type(e).__name__
                }
        
        # 전체 요약 정보
        successful_results = [r for r in results.values() if 'error' not in r]
        failed_results = [r for r in results.values() if 'error' in r]
        
        total_measurements = sum(
            r.get('summary', {}).get('measurement_count', 0) 
            for r in successful_results
        )
        
        logger.info(f"일괄 처리 완료: {len(successful_results)}개 성공, {len(failed_results)}개 실패, 총 {total_measurements}개 측정값")
        
        return results
    
    def get_statistics(self, results: Dict) -> Dict:
        """처리 결과 통계 정보 생성"""
        successful_results = [r for r in results.values() if 'error' not in r]
        failed_results = [r for r in results.values() if 'error' in r]
        
        if not successful_results:
            return {
                'total_images': len(results),
                'successful_images': 0,
                'failed_images': len(failed_results),
                'success_rate': 0.0
            }
        
        # 패턴별 통계
        pattern_stats = {}
        total_measurements = 0
        total_confidence = 0
        confidence_count = 0
        
        for result in successful_results:
            measurements = result.get('measurements', [])
            for m in measurements:
                if m['pattern_type'] != 'text':
                    pattern_type = m['pattern_type']
                    pattern_stats[pattern_type] = pattern_stats.get(pattern_type, 0) + 1
                    total_measurements += 1
                    total_confidence += m['confidence']
                    confidence_count += 1
        
        return {
            'total_images': len(results),
            'successful_images': len(successful_results),
            'failed_images': len(failed_results),
            'success_rate': len(successful_results) / len(results),
            'total_measurements': total_measurements,
            'avg_confidence': total_confidence / confidence_count if confidence_count > 0 else 0,
            'pattern_statistics': pattern_stats,
            'most_common_pattern': max(pattern_stats.items(), key=lambda x: x[1])[0] if pattern_stats else None
        }

# 편의 함수들
def create_ocr_service(languages: List[str] = ['en'], gpu: bool = False) -> OCRService:
    """OCR 서비스 인스턴스 생성"""
    return OCRService(languages=languages, gpu=gpu)

def quick_extract_measurements(image_paths: List[str], 
                             confidence_threshold: float = 0.3,
                             languages: List[str] = ['en']) -> Dict:
    """
    빠른 측정값 추출 (편의 함수)
    
    Args:
        image_paths: 이미지 파일 경로 리스트
        confidence_threshold: OCR 신뢰도 임계값
        languages: 인식할 언어 목록
        
    Returns:
        처리 결과 딕셔너리
    """
    ocr_service = create_ocr_service(languages=languages)
    return ocr_service.process_multiple_images(image_paths, confidence_threshold)

def extract_from_single_image(image_path: str, 
                            confidence_threshold: float = 0.3,
                            languages: List[str] = ['en']) -> Dict:
    """
    단일 이미지에서 측정값 추출
    
    Args:
        image_path: 이미지 파일 경로
        confidence_threshold: OCR 신뢰도 임계값
        languages: 인식할 언어 목록
        
    Returns:
        추출 결과 딕셔너리
    """
    ocr_service = create_ocr_service(languages=languages)
    
    # 텍스트 추출
    extracted_data = ocr_service.extract_text_from_image(image_path, confidence_threshold)
    
    # 측정값 추출
    measurements = ocr_service.extract_measurements(extracted_data)
    
    return {
        'file_path': str(image_path),
        'file_name': Path(image_path).name,
        'extracted_data': extracted_data,
        'measurements': measurements,
        'summary': {
            'total_texts': len(extracted_data),
            'measurement_count': len([m for m in measurements if m['pattern_type'] != 'text']),
            'text_count': len([m for m in measurements if m['pattern_type'] == 'text'])
        }
    }

# 전역 OCR 서비스 인스턴스 관리 (선택적)
_global_ocr_service = None

def get_global_ocr_service() -> OCRService:
    """전역 OCR 서비스 인스턴스 반환 (메모리 절약용)"""
    global _global_ocr_service
    if _global_ocr_service is None:
        _global_ocr_service = create_ocr_service()
    return _global_ocr_service

def reset_global_ocr_service():
    """전역 OCR 서비스 재설정"""
    global _global_ocr_service
    _global_ocr_service = None