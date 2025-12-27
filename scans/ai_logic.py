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

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    brightness = cv2.mean(gray)[0]
    if brightness < 80:
        raise ValueError("Lighting is too dark. Please face a light source.")

    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    if variance < 100:
        raise ValueError("Image is too blurry. Please hold the camera steady.")

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
            raise ValueError("No face detected. Please ensure your face is clearly visible.")
            
        landmarks = results.multi_face_landmarks[0].landmark

        nose_tip = landmarks[1].x
        left_cheek_outer = landmarks[234].x
        right_cheek_outer = landmarks[454].x

        left_dist = abs(nose_tip - left_cheek_outer)
        right_dist = abs(nose_tip - right_cheek_outer)
        
        if right_dist > 0:
            ratio = left_dist / right_dist
            if ratio < 0.6 or ratio > 1.6:
                raise ValueError("Please look straight at the camera. Do not turn your head.")

        left_eye_y = landmarks[33].y
        right_eye_y = landmarks[263].y
        
        eye_slope = abs(left_eye_y - right_eye_y)
        if eye_slope > 0.05:
            raise ValueError("Please keep your head level. Do not tilt.")

        x_values = [lm.x for lm in landmarks]
        y_values = [lm.y for lm in landmarks]

        min_x, max_x = min(x_values), max(x_values)
        min_y, max_y = min(y_values), max(y_values)

        face_width_ratio = max_x - min_x

        if min_x < 0.01 or max_x > 0.99 or min_y < 0.01 or max_y > 0.99:
             raise ValueError("You are too close to the camera (face cut off). Please move back.")

        if face_width_ratio < 0.25:
            raise ValueError("You are too far from the camera. Please move closer.")
        
        if face_width_ratio > 0.85:
            raise ValueError("You are too close to the camera. Please move back slightly.")

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
        symmetry_score = max(10, 100 - (avg_deviation * 50))
        cheek_width = get_distance(get_coords(234), get_coords(454))
        jaw_width = get_distance(get_coords(172), get_coords(397))
        puffiness_index = cheek_width / jaw_width
        normalized_puffiness = (puffiness_index - 1.0)

        return {
            "jawline_angle": round(final_jawline, 1),
            "symmetry_score": round(symmetry_score, 1),
            "puffiness_index": round(max(0.1, normalized_puffiness), 2)
        }