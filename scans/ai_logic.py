import cv2
import mediapipe as mp
import numpy as np
import math

def calculate_angle(a, b, c):
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    
    return np.degrees(angle)

def get_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def analyze_face_image(image_file):
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Could not decode image")

    height, width, _ = image.shape
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    mp_face_mesh = mp.solutions.face_mesh
    
    with mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5
    ) as face_mesh:
        
        results = face_mesh.process(rgb_image)
        
        if not results.multi_face_landmarks:
            raise ValueError("No face detected")
            
        landmarks = results.multi_face_landmarks[0].landmark

        def get_coords(index):
            return (landmarks[index].x * width, landmarks[index].y * height)

        left_jaw_angle = calculate_angle(get_coords(177), get_coords(172), get_coords(152))
        right_jaw_angle = calculate_angle(get_coords(401), get_coords(397), get_coords(152))
        final_jawline = (left_jaw_angle + right_jaw_angle) / 2
        
        pairs = [
            (33, 263), 
            (133, 362), 
            (61, 291), 
            (234, 454), 
            (172, 397), 
        ]
        
        total_deviation = 0
        mid_x = get_coords(168)[0] 
        
        for left_idx, right_idx in pairs:
            l_x, l_y = get_coords(left_idx)
            r_x, r_y = get_coords(right_idx)
            l_dist = abs(mid_x - l_x)
            r_dist = abs(r_x - mid_x)
            diff = abs(l_dist - r_dist) / ((l_dist + r_dist) / 2)
            total_deviation += diff

        avg_deviation = total_deviation / len(pairs)
        symmetry_score = max(0, 100 - (avg_deviation * 100 * 2))
        cheek_width = get_distance(get_coords(234), get_coords(454))
        jaw_width = get_distance(get_coords(172), get_coords(397))
        puffiness_index = cheek_width / jaw_width
        normalized_puffiness = (puffiness_index - 1.0)

        return {
            "jawline_angle": round(final_jawline, 1),
            "symmetry_score": round(symmetry_score, 1),
            "puffiness_index": round(max(0.1, normalized_puffiness), 2)
        }