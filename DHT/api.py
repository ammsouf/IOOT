from .Utils import send_telegram
from .models import Dht11
from .serialzers import DHT11serialize
from rest_framework.decorators import api_view
from rest_framework import status, generics
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings


@api_view(['GET'])
def Dlist(request):
    """
    /api/ : Renvoie l'historique des mesures pour les graphes.
    Retourne une LISTE JSON, directement exploitable par Chart.js.
    """
    all_data = Dht11.objects.all().order_by('dt')
    data = DHT11serialize(all_data, many=True).data
    return Response(data, status=status.HTTP_200_OK)   # Pas de {'data': ...}


@api_view(['GET'])
def latest(request):
    """
    /latest/ : Renvoie la dernière mesure (temp + hum + dt)
    Utilisée par le dashboard (cartes).
    """
    last = Dht11.objects.order_by('-dt').first()
    if last is None:
        return Response(
            {"detail": "Aucune mesure disponible"},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = DHT11serialize(last)
    return Response(serializer.data, status=status.HTTP_200_OK)


class Dhtviews(generics.CreateAPIView):
    """
    /api/post/ : Endpoint pour que le capteur envoie ses données (POST).
    """
    queryset = Dht11.objects.all()
    serializer_class = DHT11serialize

    def perform_create(self, serializer):
        instance = serializer.save()
        temp = instance.temp

        if temp > 25:
            # Envoi d'email en cas de température élevée
            try:
                send_mail(
                    subject="⚠️ Alerte Température élevée",
                    message=(
                        f"La température a atteint {temp:.1f} °C à {instance.dt}. "
                        f"je suis kaoutar belhaj et ma collegue ilham azerzar"
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=["easyyybeasyyy@gmail.com"],
                    fail_silently=False,
                )
                print("Alerte email envoyée")
            except Exception as e:
                print(f"Erreur lors de l'envoi de l'email: {e}")

            # Telegram (si tu veux l'activer)
            try:
                msg = f"⚠️ Alerte DHT11: {temp:.1f} °C (>25) à {instance.dt}"
                send_telegram(msg)
            except Exception as e:
                print(f"Erreur Telegram: {e}")


def history():
    return None
