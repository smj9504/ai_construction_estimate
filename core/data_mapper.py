"""
데이터 매핑 서비스 모듈
작업 범위와 OCR로 추출된 측정 데이터를 자동으로 매핑합니다.
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Union
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import difflib

logger = logging.getLogger(__name__)

class RoomType(Enum):
    """방 타입 열거형"""
    KITCHEN = "kitchen"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    LIVING_ROOM = "living_room"
    DINING_ROOM = "dining_room"
    BASEMENT = "basement"
    GARAGE = "garage"
    HALLWAY = "hallway"
    CLOSET = "closet"
    LAUNDRY = "laundry"
    OFFICE = "office"
    FAMILY_ROOM = "family_room"
    MASTER_BEDROOM = "master_bedroom"
    GUEST_ROOM = "guest_room"
    POWDER_ROOM = "powder_room"
    OTHER = "other"

class WorkType(Enum):
    """작업 타입 열거형"""
    CABINET_REPLACEMENT = "cabinet_replacement"
    FLOORING = "flooring"
    TILE_WORK = "tile_work"
    PAINT = "paint"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    DRYWALL = "drywall"
    TRIM_WORK = "trim_work"
    COUNTERTOP = "countertop"
    FIXTURE_REPLACEMENT = "fixture_replacement"
    DEMOLITION = "demolition"
    INSULATION = "insulation"
    OTHER = "other"

@dataclass
class WorkScope:
    """작업 범위 데이터 클래스"""
    room_name: str
    room_type: RoomType
    work_description: str
    work_types: List[WorkType]
    priority: int = 1
    notes: str = ""
    estimated_area: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'room_name': self.room_name,
            'room_type': self.room_type.value,
            'work_description': self.work_description,
            'work_types': [wt.value for wt in self.work_types],
            'priority': self.priority,
            'notes': self.notes,
            'estimated_area': self.estimated_area
        }

@dataclass
class MeasurementData:
    """측정 데이터 클래스"""
    room_identifier: str
    measurement_type: str  # length, width, height, area, dimension
    value: float
    unit: str
    confidence: float
    source_image: str
    pattern_type: str
    original_text: str
    position: Dict
    
    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return asdict(self)

class DataMapper:
    """작업범위와 측정 데이터를 매핑하는 서비스"""
    
    def __init__(self):
        """데이터 매퍼 초기화"""
        logger.info("DataMapper 초기화")
        
        # 방 타입 키워드 매핑 (우선순위 순서)
        self.room_keywords = {
            RoomType.KITCHEN: [
                'kitchen', 'kitc', 'cook', 'cabinet', 'countertop', 'pantry'
            ],
            RoomType.MASTER_BEDROOM: [
                'master', 'master bedroom', 'master bed', 'mbr', 'master br'
            ],
            RoomType.BEDROOM: [
                'bedroom', 'bed', 'br', 'guest room', 'guest bed', 'bdrm'
            ],
            RoomType.BATHROOM: [
                'bathroom', 'bath', 'toilet', 'shower', 'restroom', 'washroom'
            ],
            RoomType.POWDER_ROOM: [
                'powder', 'powder room', 'half bath', 'guest bath'
            ],
            RoomType.LIVING_ROOM: [
                'living', 'living room', 'great room', 'lounge', 'front room'
            ],
            RoomType.FAMILY_ROOM: [
                'family', 'family room', 'den', 'rec room', 'recreation'
            ],
            RoomType.DINING_ROOM: [
                'dining', 'dining room', 'dinner', 'eat'
            ],
            RoomType.BASEMENT: [
                'basement', 'cellar', 'lower', 'downstairs', 'below'
            ],
            RoomType.GARAGE: [
                'garage', 'car', 'parking'
            ],
            RoomType.HALLWAY: [
                'hallway', 'hall', 'corridor', 'passage'
            ],
            RoomType.CLOSET: [
                'closet', 'storage', 'walk-in'
            ],
            RoomType.LAUNDRY: [
                'laundry', 'wash', 'utility'
            ],
            RoomType.OFFICE: [
                'office', 'study', 'den', 'work'
            ]
        }
        
        # 작업 타입 키워드 매핑
        self.work_keywords = {
            WorkType.CABINET_REPLACEMENT: [
                'cabinet', 'cabinets', 'cupboard', 'replace cabinet', 'new cabinet'
            ],
            WorkType.FLOORING: [
                'floor', 'flooring', 'hardwood', 'carpet', 'laminate', 
                'vinyl', 'tile floor', 'wood floor'
            ],
            WorkType.TILE_WORK: [
                'tile', 'tiles', 'ceramic', 'porcelain', 'backsplash', 'tiling'
            ],
            WorkType.PAINT: [
                'paint', 'painting', 'primer', 'color', 'wall paint'
            ],
            WorkType.ELECTRICAL: [
                'electrical', 'electric', 'wiring', 'outlet', 'switch', 'light'
            ],
            WorkType.PLUMBING: [
                'plumbing', 'pipe', 'faucet', 'sink', 'toilet', 'water'
            ],
            WorkType.DRYWALL: [
                'drywall', 'sheetrock', 'wall', 'ceiling'
            ],
            WorkType.TRIM_WORK: [
                'trim', 'molding', 'baseboard', 'crown', 'casing'
            ],
            WorkType.COUNTERTOP: [
                'countertop', 'counter', 'granite', 'quartz', 'marble'
            ],
            WorkType.FIXTURE_REPLACEMENT: [
                'fixture', 'replace', 'new', 'install'
            ],
            WorkType.DEMOLITION: [
                'demo', 'demolition', 'remove', 'tear down', 'gut'
            ],
            WorkType.INSULATION: [
                'insulation', 'insulate', 'foam', 'fiberglass'
            ]
        }
        
        logger.info("DataMapper 초기화 완료")
    
    def parse_work_scope(self, scope_text: str) -> List[WorkScope]:
        """
        작업 범위 텍스트를 파싱하여 구조화된 데이터로 변환
        
        Args:
            scope_text: 작업 범위 텍스트
            
        Returns:
            WorkScope 객체 리스트
        """
        work_scopes = []
        
        if not scope_text or not scope_text.strip():
            logger.warning("빈 작업 범위 텍스트")
            return work_scopes
        
        # 줄 단위로 분리 및 정리
        lines = [line.strip() for line in scope_text.split('\n') if line.strip()]
        
        logger.info(f"작업 범위 파싱 시작: {len(lines)}개 라인")
        
        for i, line in enumerate(lines):
            try:
                # 방 정보 추출
                room_info = self._extract_room_info(line)
                
                if room_info:
                    work_scope = WorkScope(
                        room_name=room_info['name'],
                        room_type=room_info['type'],
                        work_description=room_info['work'],
                        work_types=room_info['work_types'],
                        priority=i + 1,
                        notes=room_info.get('notes', '')
                    )
                    work_scopes.append(work_scope)
                    logger.debug(f"작업 범위 추가: {work_scope.room_name} - {work_scope.work_description}")
                    
            except Exception as e:
                logger.warning(f"작업 범위 파싱 실패: {line} - {e}")
                # 파싱 실패 시에도 기본 정보로 추가
                work_scope = WorkScope(
                    room_name=line,
                    room_type=RoomType.OTHER,
                    work_description="General work",
                    work_types=[WorkType.OTHER],
                    priority=i + 1,
                    notes="Parsing failed"
                )
                work_scopes.append(work_scope)
        
        logger.info(f"작업 범위 파싱 완료: {len(work_scopes)}개 항목")
        return work_scopes
    
    def _extract_room_info(self, text: str) -> Optional[Dict]:
        """텍스트에서 방 정보 추출"""
        if not text:
            return None
            
        # 일반적인 패턴들 시도
        patterns = [
            r"(.+?)\s*-\s*(.+)",      # "Kitchen - cabinet replacement"
            r"(.+?):\s*(.+)",         # "Kitchen: cabinet replacement"
            r"(.+?)\s+(.+)",          # "Kitchen cabinet replacement"
        ]
        
        room_part = ""
        work_part = ""
        
        # 패턴 매칭 시도
        for pattern in patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                room_part = match.group(1).strip()
                work_part = match.group(2).strip()
                break
        
        # 패턴 매칭 실패 시 전체를 방 이름으로 처리
        if not room_part:
            room_part = text
            work_part = "General work"
        
        # 방 타입 식별
        room_type = self._identify_room_type(room_part + " " + work_part)
        
        # 작업 타입들 식별
        work_types = self._identify_work_types(work_part)
        
        return {
            'name': room_part,
            'type': room_type,
            'work': work_part,
            'work_types': work_types,
            'notes': ''
        }
    
    def _identify_room_type(self, text: str) -> RoomType:
        """텍스트에서 방 타입 식별"""
        text_lower = text.lower()
        
        # 우선순위 순서로 검사 (구체적인 것부터)
        for room_type, keywords in self.room_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    logger.debug(f"방 타입 식별: '{text}' -> {room_type.value} (키워드: {keyword})")
                    return room_type
        
        logger.debug(f"방 타입 식별 실패: '{text}' -> OTHER")
        return RoomType.OTHER
    
    def _identify_work_types(self, text: str) -> List[WorkType]:
        """텍스트에서 작업 타입들 식별"""
        text_lower = text.lower()
        identified_types = []
        
        for work_type, keywords in self.work_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    identified_types.append(work_type)
                    logger.debug(f"작업 타입 식별: '{text}' -> {work_type.value} (키워드: {keyword})")
                    break  # 각 타입당 하나의 키워드만 매칭
        
        # 아무것도 식별되지 않으면 OTHER 추가
        if not identified_types:
            identified_types.append(WorkType.OTHER)
            logger.debug(f"작업 타입 식별 실패: '{text}' -> OTHER")
        
        return identified_types
    
    def process_measurements(self, ocr_results: Dict) -> List[MeasurementData]:
        """
        OCR 결과에서 측정 데이터 추출 및 구조화
        
        Args:
            ocr_results: OCR 서비스의 process_multiple_images() 결과
            
        Returns:
            MeasurementData 객체 리스트
        """
        measurements = []
        
        if not ocr_results:
            logger.warning("빈 OCR 결과")
            return measurements
        
        logger.info(f"측정 데이터 처리 시작: {len(ocr_results)}개 이미지")
        
        for image_key, image_data in ocr_results.items():
            if 'error' in image_data:
                logger.warning(f"이미지 처리 오류 건너뛰기: {image_key} - {image_data['error']}")
                continue
            
            file_path = image_data.get('file_path', 'unknown')
            measurement_items = image_data.get('measurements', [])
            
            logger.debug(f"이미지 {image_key}: {len(measurement_items)}개 측정 항목")
            
            for item in measurement_items:
                if item.get('pattern_type') == 'text':
                    continue  # 측정값이 아닌 텍스트는 건너뛰기
                
                try:
                    # 방 식별자 추출
                    room_id = self._extract_room_identifier(file_path, item)
                    
                    # 측정 타입 결정
                    measurement_type = self._determine_measurement_type(item)
                    
                    # 값과 단위 추출
                    value, unit = self._extract_value_and_unit(item)
                    
                    if value is not None:
                        measurement = MeasurementData(
                            room_identifier=room_id,
                            measurement_type=measurement_type,
                            value=value,
                            unit=unit,
                            confidence=item.get('confidence', 0.0),
                            source_image=file_path,
                            pattern_type=item.get('pattern_type', 'unknown'),
                            original_text=item.get('original_text', ''),
                            position=item.get('position', {})
                        )
                        measurements.append(measurement)
                        logger.debug(f"측정 데이터 추가: {room_id} - {measurement_type} = {value} {unit}")
                        
                except Exception as e:
                    logger.warning(f"측정 데이터 처리 실패: {item} - {e}")
        
        logger.info(f"측정 데이터 처리 완료: {len(measurements)}개 항목")
        return measurements
    
    def _extract_room_identifier(self, file_path: str, measurement_item: Dict) -> str:
        """파일명이나 측정 항목에서 방 식별자 추출"""
        # 1. 파일명에서 방 정보 추출 시도
        filename = Path(file_path).stem.lower()
        
        # 파일명에서 방 타입 키워드 검색
        for room_type, keywords in self.room_keywords.items():
            for keyword in keywords:
                if keyword in filename:
                    logger.debug(f"파일명에서 방 식별: {filename} -> {room_type.value}")
                    return room_type.value
        
        # 2. 측정 항목의 텍스트에서 방 정보 추출 시도
        text = measurement_item.get('original_text', '').lower()
        for room_type, keywords in self.room_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    logger.debug(f"텍스트에서 방 식별: {text} -> {room_type.value}")
                    return room_type.value
        
        # 3. 파일명 기반 기본 식별자
        if filename:
            return filename
        
        # 4. 최후 수단
        return 'unknown'
    
    def _determine_measurement_type(self, measurement_item: Dict) -> str:
        """측정 항목에서 측정 타입 결정"""
        pattern_type = measurement_item.get('pattern_type', '')
        original_text = measurement_item.get('original_text', '').lower()
        
        # 패턴 타입 기반 판단
        if pattern_type == 'area_sqft' or pattern_type == 'area_sqin':
            return 'area'
        elif pattern_type == 'dimensions':
            return 'dimensions'  # width x height
        
        # 텍스트 내용 기반 판단
        if any(keyword in original_text for keyword in ['width', 'w', 'wide']):
            return 'width'
        elif any(keyword in original_text for keyword in ['height', 'h', 'high', 'tall']):
            return 'height'
        elif any(keyword in original_text for keyword in ['length', 'l', 'long']):
            return 'length'
        elif any(keyword in original_text for keyword in ['depth', 'd', 'deep']):
            return 'depth'
        elif any(keyword in original_text for keyword in ['area', 'sq', 'square']):
            return 'area'
        else:
            return 'dimension'  # 일반적인 치수
    
    def _extract_value_and_unit(self, measurement_item: Dict) -> Tuple[Optional[float], str]:
        """측정 항목에서 값과 단위 추출"""
        pattern_type = measurement_item.get('pattern_type', '')
        
        # 패턴별 값 추출
        if 'total_inches' in measurement_item:
            return float(measurement_item['total_inches']), 'inches'
        elif 'total_feet' in measurement_item:
            return float(measurement_item['total_feet']), 'feet'
        elif 'decimal_feet' in measurement_item:
            return float(measurement_item['decimal_feet']), 'feet'
        elif 'area' in measurement_item:
            unit = measurement_item.get('unit', 'sq_ft')
            return float(measurement_item['area']), unit
        elif pattern_type == 'dimensions' and 'width' in measurement_item and 'height' in measurement_item:
            # 면적으로 계산
            width = measurement_item.get('width', 0)
            height = measurement_item.get('height', 0)
            return float(width * height), 'sq_unit'
        elif 'decimal_value' in measurement_item:
            return float(measurement_item['decimal_value']), 'unit'
        elif 'integer_value' in measurement_item:
            return float(measurement_item['integer_value']), 'unit'
        
        return None, 'unknown'
    
    def map_scope_to_measurements(self, work_scopes: List[WorkScope], 
                                measurements: List[MeasurementData]) -> Dict:
        """
        작업 범위와 측정 데이터 매핑
        
        Args:
            work_scopes: 파싱된 작업 범위 리스트
            measurements: 추출된 측정 데이터 리스트
            
        Returns:
            매핑 결과 딕셔너리
        """
        logger.info(f"데이터 매핑 시작: {len(work_scopes)}개 작업범위, {len(measurements)}개 측정값")
        
        mapping_result = {
            'work_scopes': [scope.to_dict() for scope in work_scopes],
            'measurements': [measurement.to_dict() for measurement in measurements],
            'mappings': [],
            'unmatched_measurements': [],
            'unmatched_scopes': [],
            'summary': {}
        }
        
        # 측정 데이터를 방별로 그룹화
        measurement_groups = self._group_measurements_by_room(measurements)
        
        # 매핑 수행
        matched_rooms = set()
        matched_scopes = []
        
        for scope in work_scopes:
            best_match = self._find_best_measurement_match(
                scope.room_name, 
                scope.room_type, 
                measurement_groups
            )
            
            if best_match:
                room_id, confidence = best_match
                mapping_result['mappings'].append({
                    'work_scope': scope.to_dict(),
                    'measurements': [m.to_dict() for m in measurement_groups[room_id]],
                    'room_identifier': room_id,
                    'match_confidence': confidence,
                    'match_method': self._get_match_method(scope.room_name, scope.room_type, room_id)
                })
                matched_rooms.add(room_id)
                matched_scopes.append(scope)
                logger.debug(f"매핑 성공: {scope.room_name} -> {room_id} (신뢰도: {confidence:.2f})")
        
        # 매핑되지 않은 측정값들
        for room_id, measurements_list in measurement_groups.items():
            if room_id not in matched_rooms:
                mapping_result['unmatched_measurements'].append({
                    'room_identifier': room_id,
                    'measurements': [m.to_dict() for m in measurements_list],
                    'measurement_count': len(measurements_list)
                })
                logger.debug(f"미매핑 측정값: {room_id} ({len(measurements_list)}개)")
        
        # 매핑되지 않은 작업 범위들
        unmatched_scopes = [scope for scope in work_scopes if scope not in matched_scopes]
        for scope in unmatched_scopes:
            mapping_result['unmatched_scopes'].append(scope.to_dict())
            logger.debug(f"미매핑 작업범위: {scope.room_name}")
        
        # 요약 정보 생성
        mapping_result['summary'] = self._generate_mapping_summary(
            work_scopes, measurements, mapping_result
        )
        
        logger.info(f"데이터 매핑 완료: {mapping_result['summary']}")
        return mapping_result
    
    def _group_measurements_by_room(self, measurements: List[MeasurementData]) -> Dict[str, List[MeasurementData]]:
        """측정 데이터를 방별로 그룹화"""
        groups = {}
        for measurement in measurements:
            room_id = measurement.room_identifier
            if room_id not in groups:
                groups[room_id] = []
            groups[room_id].append(measurement)
        
        logger.debug(f"측정값 그룹화: {len(groups)}개 그룹")
        return groups
    
    def _find_best_measurement_match(self, room_name: str, room_type: RoomType, 
                                   measurement_groups: Dict[str, List[MeasurementData]]) -> Optional[Tuple[str, float]]:
        """작업 범위에 가장 적합한 측정 데이터 그룹 찾기"""
        room_name_lower = room_name.lower()
        
        candidates = []
        
        for room_id in measurement_groups.keys():
            room_id_lower = room_id.lower()
            
            # 1. 정확한 문자열 매칭 (최고 점수)
            if room_name_lower == room_id_lower:
                candidates.append((room_id, 1.0, 'exact_match'))
                continue
            
            # 2. 포함 관계 매칭
            if room_name_lower in room_id_lower or room_id_lower in room_name_lower:
                similarity = max(len(room_name_lower), len(room_id_lower)) / \
                           (len(room_name_lower) + len(room_id_lower))
                candidates.append((room_id, 0.8 + similarity * 0.1, 'substring_match'))
                continue
            
            # 3. 방 타입 키워드 매칭
            room_type_keywords = self.room_keywords.get(room_type, [])
            for keyword in room_type_keywords:
                if keyword in room_id_lower:
                    candidates.append((room_id, 0.6, 'room_type_match'))
                    break
            
            # 4. 유사도 기반 매칭 (문자열 유사성)
            similarity = difflib.SequenceMatcher(None, room_name_lower, room_id_lower).ratio()
            if similarity > 0.3:  # 30% 이상 유사한 경우만
                candidates.append((room_id, similarity * 0.5, 'similarity_match'))
        
        if not candidates:
            return None
        
        # 가장 높은 점수의 매칭 반환
        best_match = max(candidates, key=lambda x: x[1])
        return best_match[0], best_match[1]
    
    def _get_match_method(self, room_name: str, room_type: RoomType, room_id: str) -> str:
        """매칭 방법 결정"""
        room_name_lower = room_name.lower()
        room_id_lower = room_id.lower()
        
        if room_name_lower == room_id_lower:
            return 'exact_match'
        elif room_name_lower in room_id_lower or room_id_lower in room_name_lower:
            return 'substring_match'
        elif any(keyword in room_id_lower for keyword in self.room_keywords.get(room_type, [])):
            return 'room_type_match'
        else:
            return 'similarity_match'
    
    def _generate_mapping_summary(self, work_scopes: List[WorkScope], 
                                measurements: List[MeasurementData], 
                                mapping_result: Dict) -> Dict:
        """매핑 결과 요약 정보 생성"""
        successful_mappings = len(mapping_result['mappings'])
        unmatched_measurements = len(mapping_result['unmatched_measurements'])
        unmatched_scopes = len(mapping_result['unmatched_scopes'])
        
        # 신뢰도 통계
        confidences = [m['match_confidence'] for m in mapping_result['mappings']]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # 매칭 방법 통계
        match_methods = [m['match_method'] for m in mapping_result['mappings']]
        method_counts = {method: match_methods.count(method) for method in set(match_methods)}
        
        # 측정값 타입 통계
        measurement_types = [m.measurement_type for m in measurements]
        type_counts = {mtype: measurement_types.count(mtype) for mtype in set(measurement_types)}
        
        return {
            'total_work_scopes': len(work_scopes),
            'total_measurements': len(measurements),
            'successful_mappings': successful_mappings,
            'unmatched_measurements': unmatched_measurements,
            'unmatched_scopes': unmatched_scopes,
            'mapping_success_rate': successful_mappings / len(work_scopes) if work_scopes else 0,
            'average_match_confidence': avg_confidence,
            'match_method_statistics': method_counts,
            'measurement_type_statistics': type_counts,
            'quality_score': self._calculate_quality_score(mapping_result)
        }
    
    def _calculate_quality_score(self, mapping_result: Dict) -> float:
        """매핑 품질 점수 계산 (0-1)"""
        mappings = mapping_result['mappings']
        if not mappings:
            return 0.0
        
        # 신뢰도 점수 (40%)
        confidences = [m['match_confidence'] for m in mappings]
        confidence_score = sum(confidences) / len(confidences)
        
        # 완성도 점수 (40%)
        total_scopes = len(mapping_result['work_scopes'])
        completion_score = len(mappings) / total_scopes if total_scopes > 0 else 0
        
        # 정확도 점수 (20%) - exact_match와 substring_match에 가중치
        exact_matches = sum(1 for m in mappings if m['match_method'] == 'exact_match')
        substring_matches = sum(1 for m in mappings if m['match_method'] == 'substring_match')
        accuracy_score = (exact_matches * 1.0 + substring_matches * 0.8) / len(mappings)
        
        quality_score = (confidence_score * 0.4 + completion_score * 0.4 + accuracy_score * 0.2)
        return min(1.0, max(0.0, quality_score))

# 편의 함수들
def create_data_mapper() -> DataMapper:
    """데이터 매퍼 인스턴스 생성"""
    return DataMapper()

def quick_mapping(scope_text: str, ocr_results: Dict) -> Dict:
    """
    빠른 매핑 (편의 함수)
    
    Args:
        scope_text: 작업 범위 텍스트
        ocr_results: OCR 서비스 결과
        
    Returns:
        매핑 결과 딕셔너리
    """
    mapper = create_data_mapper()
    work_scopes = mapper.parse_work_scope(scope_text)
    measurements = mapper.process_measurements(ocr_results)
    return mapper.map_scope_to_measurements(work_scopes, measurements)

def parse_scope_only(scope_text: str) -> List[Dict]:
    """작업 범위만 파싱 (편의 함수)"""
    mapper = create_data_mapper()
    work_scopes = mapper.parse_work_scope(scope_text)
    return [scope.to_dict() for scope in work_scopes]

def process_measurements_only(ocr_results: Dict) -> List[Dict]:
    """측정 데이터만 처리 (편의 함수)"""
    mapper = create_data_mapper()
    measurements = mapper.process_measurements(ocr_results)
    return [measurement.to_dict() for measurement in measurements]

# 전역 데이터 매퍼 인스턴스 (선택적)
_global_data_mapper = None

def get_global_data_mapper() -> DataMapper:
    """전역 데이터 매퍼 인스턴스 반환"""
    global _global_data_mapper
    if _global_data_mapper is None:
        _global_data_mapper = create_data_mapper()
    return _global_data_mapper

def reset_global_data_mapper():
    """전역 데이터 매퍼 재설정"""
    global _global_data_mapper
    _global_data_mapper = None