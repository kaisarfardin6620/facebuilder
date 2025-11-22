from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from scans.models import FaceScan, UserGoal
from openai import OpenAI
from .models import ChatMessage
from .serializers import ChatMessageSerializer

class ChatCoachView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        messages = ChatMessage.objects.filter(user=request.user).order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user_message = request.data.get('message')
        if not user_message:
            return Response({"error": "Message required"}, status=status.HTTP_400_BAD_REQUEST)

        ChatMessage.objects.create(user=request.user, sender='USER', message=user_message)

        scan = FaceScan.objects.filter(user=request.user).last()
        goal = UserGoal.objects.filter(user=request.user).first()
        
        context_str = "User Data: "
        if scan:
            context_str += f"Jawline Angle: {scan.jawline_angle}, Symmetry: {scan.symmetry_score}%, Puffiness: {scan.puffiness_index}. "
        if goal:
            context_str += f"Targets: Jaw {goal.target_jawline}, Sym {goal.target_symmetry}. "

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"You are FaceCoach. User stats: {context_str}. Keep answers short, motivating, and focused on facial fitness."},
                    {"role": "user", "content": user_message}
                ]
            )
            
            ai_reply = response.choices[0].message.content

            ChatMessage.objects.create(user=request.user, sender='AI', message=ai_reply)

            return Response({"reply": ai_reply}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": "AI Service Error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)