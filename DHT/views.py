from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import json
import traceback
from django.utils import timezone
from datetime import timedelta

from rest_framework.decorators import api_view
from rest_framework import status as drf_status
from .models import Dht11, Measurement, Incident, IncidentHistory
from .serialzers import DHT11serialize, IncidentSerializer


@csrf_exempt
def save_measurements(request):
    print("=" * 70)
    print("🔍 DEBUG: save_measurements called")
    print("=" * 70)

    if request.method == 'POST':
        try:
            print("✓ Method is POST")
            data = json.loads(request.body)
            print(f"✓ Data received: {data}")

            temperature = data.get("temperature")
            humidity = data.get("humedite")
            print(f"✓ Temperature: {temperature}, Humidity: {humidity}")

            # Enregistrer dans la base de données
            instance = Dht11.objects.create(temp=temperature, hum=humidity)
            print(
                f"✓ Mesure enregistrée: ID={instance.id}, Temp={temperature}°C, Hum={humidity}%, DateTime={instance.dt}")

            # Vérifier si la température est hors de la plage normale (< 2 ou > 8)
            if temperature < 2 or temperature > 8:
                print(f"⚠️ Temperature OUT OF RANGE: {temperature} (should be between 2-8°C)")

                # Chercher un incident actif
                active_incident = Incident.objects.filter(is_active=True).first()
                print(f"🔍 Searching for active incident...")
                print(f"   Result: {active_incident}")

                if active_incident is None:
                    print("➕ NO active incident found - Creating NEW incident...")
                    active_incident = Incident.objects.create(
                        temperature=temperature,
                        humidity=humidity,
                        status='en_cours',
                        is_active=True,
                        counter=1
                    )
                    print(f"✅ NEW incident created:")
                    print(f"   - ID: {active_incident.incident_id}")
                    print(f"   - Counter: {active_incident.counter}")
                    print(f"   - Status: {active_incident.status}")
                    print(f"   - is_active: {active_incident.is_active}")

                    # LOG CREATION IN HISTORY
                    IncidentHistory.objects.create(
                        incident=active_incident,
                        action='created',
                        description=f"Incident créé - Température: {temperature}°C, Humidité: {humidity}%",
                        temperature=temperature,
                        humidity=humidity,
                        counter_value=1
                    )
                    print("📝 History: Incident creation logged")

                else:
                    print(f"📈 ACTIVE incident found: #{active_incident.incident_id}")
                    print(f"   - Old counter: {active_incident.counter}")
                    print(f"   - Old temp: {active_incident.temperature}")

                    old_counter = active_incident.counter
                    active_incident.counter += 1
                    active_incident.temperature = temperature
                    active_incident.humidity = humidity
                    active_incident.save()

                    print(f"   - NEW counter: {active_incident.counter}")
                    print(f"   - NEW temp: {active_incident.temperature}")

                    # LOG INCREMENT IN HISTORY
                    IncidentHistory.objects.create(
                        incident=active_incident,
                        action='counter_increment',
                        description=f"Alerte #{active_incident.counter} - Température: {temperature}°C, Humidité: {humidity}%",
                        temperature=temperature,
                        humidity=humidity,
                        counter_value=active_incident.counter
                    )
                    print(f"📝 History: Counter increment logged (from {old_counter} to {active_incident.counter})")

                # Envoyer l'email
                print("📧 Preparing to send alert email...")
                send_alert_email(active_incident, temperature, humidity, instance.dt)
                print("✅ Alert email function completed")

            else:
                # Température entre 2 et 8°C - vérifier s'il y a un incident actif à fermer
                print(f"✅ Temperature IN NORMAL RANGE: {temperature} (between 2-8°C)")
                active_incident = Incident.objects.filter(is_active=True).first()
                print(f"🔍 Checking for active incident to close...")
                print(f"   Result: {active_incident}")

                if active_incident is not None:
                    print(f"🔒 CLOSING incident #{active_incident.incident_id}")
                    print(f"   - Old status: {active_incident.status}")
                    print(f"   - Old is_active: {active_incident.is_active}")

                    # Fermer l'incident et changer le status
                    active_incident.is_active = False
                    active_incident.status = 'resolu'
                    active_incident.end_time = timezone.now()  # SET END TIME
                    active_incident.save()

                    print(f"   - NEW status: {active_incident.status}")
                    print(f"   - NEW is_active: {active_incident.is_active}")
                    print(f"   - End time: {active_incident.end_time}")
                    print(f"   - Duration: {active_incident.duration()}")
                    print(f"✅ Incident #{active_incident.incident_id} successfully closed and marked as RESOLU")

                    # LOG RESOLUTION IN HISTORY
                    IncidentHistory.objects.create(
                        incident=active_incident,
                        action='resolved',
                        description=f"Incident résolu - Température normalisée: {temperature}°C, Humidité: {humidity}% - Durée: {active_incident.duration()} - Total alertes: {active_incident.counter}",
                        temperature=temperature,
                        humidity=humidity,
                        counter_value=active_incident.counter
                    )
                    print("📝 History: Incident resolution logged")

                    # Envoyer un email de notification de fermeture
                    print("📧 Sending closure notification email...")
                    try:
                        send_mail(
                            subject="✅ Incident Résolu - Température Normalisée",
                            message=(
                                f"L'incident #{active_incident.incident_id} a été résolu.\n\n"
                                f"Status: RÉSOLU\n"
                                f"Température actuelle: {temperature:.1f}°C\n"
                                f"Humidité actuelle: {humidity}%\n"
                                f"Date de résolution: {active_incident.end_time}\n"
                                f"Durée de l'incident: {active_incident.duration()}\n"
                                f"Nombre total d'alertes: {active_incident.counter}\n\n"
                                f"La température est revenue à la normale (entre 2°C et 8°C).\n\n"
                                f"Signalé par: Aymen Mechida et Adnane"
                            ),
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=["amallahsoufiane1@gmail.com"],
                            fail_silently=False,
                        )
                        print("✅ Closure email sent successfully")
                    except Exception as e:
                        print(f"❌ ERROR sending closure email: {e}")
                        traceback.print_exc()
                else:
                    print("ℹ️ No active incident to close")

            print("=" * 70)
            print("✅ save_measurements completed successfully")
            print("=" * 70)

            return JsonResponse({
                "message": "Données enregistrées avec succès",
                "temperature": temperature,
                "humidity": humidity
            }, status=201)

        except json.JSONDecodeError as e:
            print(f"❌ JSON Decode Error: {e}")
            return JsonResponse({"error": "JSON invalide"}, status=400)
        except Exception as e:
            print(f"❌ EXCEPTION in save_measurements: {e}")
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=400)

    print("❌ Method is not POST")
    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


def send_alert_email(incident, temperature, humidity, timestamp):
    """
    Envoie un email d'alerte en fonction du compteur de l'incident
    - counter < 4: operator1 seulement
    - counter entre 4 et 6: operator1 et operator2
    - counter > 6: operator1, operator2 et operator3
    """
    print("\n" + "=" * 70)
    print("📧 DEBUG: send_alert_email function called")
    print("=" * 70)

    counter = incident.counter
    print(f"📊 Incident details:")
    print(f"   - Incident ID: {incident.incident_id}")
    print(f"   - Counter: {counter}")
    print(f"   - Temperature: {temperature}")
    print(f"   - Humidity: {humidity}")
    print(f"   - Timestamp: {timestamp}")

    # Déterminer les destinataires en fonction du compteur
    if counter < 4:
        recipients = ["amallahsoufiane1@gmail.com"]
        level = "ALERTE NIVEAU 1"
        print(f"🔵 Level 1 Alert (counter < 4)")
    elif 4 <= counter <= 6:
        recipients = ["amallahsoufiane1@gmail.com", "operator2@example.com"]
        level = "ALERTE NIVEAU 2"
        print(f"🟡 Level 2 Alert (counter 4-6)")
    else:
        recipients = ["amallahsoufiane1@gmail.com", "operator2@example.com", "operator3@example.com"]
        level = "ALERTE NIVEAU 3 - CRITIQUE"
        print(f"🔴 Level 3 Alert - CRITICAL (counter > 6)")

    print(f"📧 Email configuration:")
    print(f"   - Level: {level}")
    print(f"   - Recipients: {recipients}")
    print(f"   - From: {settings.EMAIL_HOST_USER}")

    email_subject = f"🚨 {level} - Incident #{incident.incident_id}"
    email_message = (
        f"{level}\n"
        f"{'=' * 50}\n\n"
        f"Incident ID: {incident.incident_id}\n"
        f"Compteur d'alertes: {counter}\n"
        f"Température: {temperature:.1f}°C\n"
        f"Humidité: {humidity}%\n"
        f"Date et heure: {timestamp}\n\n"
        f"⚠️ La température est hors de la plage normale (2-8°C)\n\n"
        f"Signalé par: Aymen Mechida et Adnane"
    )

    print(f"📝 Email content:")
    print(f"   - Subject: {email_subject}")
    print(f"   - Message length: {len(email_message)} characters")
    print(f"   - Message preview (first 150 chars):")
    print(f"     {email_message[:150]}...")

    try:
        print("\n🔄 Attempting to send email...")
        print(f"   Using EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"   Using EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"   Using EMAIL_PORT: {settings.EMAIL_PORT}")

        result = send_mail(
            subject=email_subject,
            message=email_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipients,
            fail_silently=False,
        )

        print(f"✅ Email sent SUCCESSFULLY!")
        print(f"   - send_mail() returned: {result}")
        print(f"   - Number of emails sent: {result}")
        print(f"   - Recipients: {', '.join(recipients)}")

    except Exception as e:
        print(f"❌ ERROR sending email:")
        print(f"   - Error type: {type(e).__name__}")
        print(f"   - Error message: {str(e)}")
        print(f"\n📋 Full traceback:")
        traceback.print_exc()

    print("=" * 70)
    print("📧 send_alert_email function completed")
    print("=" * 70 + "\n")


@api_view(['GET'])
def latest_incident(request):
    try:
        active_incident = Incident.objects.filter(is_active=True).last()

        if active_incident is None:
            return JsonResponse({
                "status": "Aucun incident en cours",
                "start_time": None
            }, status=404)

        incident_data = {
            "incident_id": active_incident.incident_id,
            "status": active_incident.status,
            "start_time": active_incident.start_time.isoformat(),
            "counter": active_incident.counter,
            "temperature": active_incident.temperature,
            "humidity": active_incident.humidity
        }
        return JsonResponse(incident_data, status=200)

    except Exception as e:
        return JsonResponse({
            "error": f"Erreur lors de l'accès aux incidents: {str(e)}"
        }, status=500)


@login_required
@never_cache
def incident_dashboard(request):
    try:
        active_incident = Incident.objects.filter(is_active=True).last()
        return render(request, 'dashboard.html', {
            'active_incident': active_incident
        })
    except Exception as e:
        return render(request, 'dashboard.html', {
            'error': f"Erreur: {str(e)}"
        })


def test(request):
    return HttpResponse("je suis Aymen Mechida")


@login_required
@never_cache
def dashboard(request):
    try:
        last_measurement = Measurement.objects.latest('timestamp')
    except Measurement.DoesNotExist:
        last_measurement = None

    # Always show the LAST incident (active or closed)
    last_incident = Incident.objects.all().order_by('-start_time').first()

    context = {
        'last_measurement': last_measurement,
        'active_incident': last_incident
    }
    return render(request, "dashboard.html", context)


@login_required
@never_cache
def graph_hum(request):
    return render(request, "graph_hum.html")


@login_required
@never_cache
def graph_temp(request):
    return render(request, "graph_temp.html")


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Nom d\'utilisateur ou mot de passe incorrect.'
                })
        else:
            return render(request, 'login.html', {
                'form': form,
                'error': 'Formulaire invalide.'
            })
    else:
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
@never_cache
def incident_archive(request):
    try:
        all_incidents = Incident.objects.all().order_by('-start_time')
        return render(request, 'incident_archive.html', {
            'incidents': all_incidents
        })
    except Exception as e:
        return render(request, 'incident_archive.html', {
            'error': f"Erreur lors de la récupération des incidents: {str(e)}"
        })


@login_required
@never_cache
def incident_detail(request, incident_id):
    """View detailed incident with full history"""
    try:
        incident = Incident.objects.get(incident_id=incident_id)
        history = incident.history.all()  # Get all history entries

        context = {
            'incident': incident,
            'history': history
        }
        return render(request, 'incident_detail.html', context)
    except Incident.DoesNotExist:
        return render(request, 'incident_detail.html', {
            'error': 'Incident non trouvé'
        })


@csrf_exempt
def create_incident(request):
    """
    Cette fonction n'est plus utilisée directement car les incidents
    sont créés automatiquement par save_measurements
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            temperature = data.get('temperature')
            humidity = data.get('humidity')
            incident_status = data.get('status')
            start_time = data.get('start_time')

            incident = Incident.objects.create(
                temperature=temperature,
                humidity=humidity,
                status=incident_status,
                start_time=start_time,
                is_active=True,
                counter=1
            )

            return JsonResponse({
                'incident_id': incident.incident_id,
                'status': incident.status,
                'start_time': incident.start_time.isoformat(),
                'counter': incident.counter
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON invalide'}, status=400)
        except Exception as e:
            print(f"Erreur create_incident: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@csrf_exempt
def submit_comment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            incident_id = data.get('incident_id')
            comment = data.get('comment')

            incident = Incident.objects.get(incident_id=incident_id)

            # Check if this is adding a new comment or updating
            action = 'comment_added' if not incident.operator_1_comment else 'comment_updated'
            old_comment = incident.operator_1_comment or "Aucun"

            incident.operator_1_comment = comment
            incident.save()

            # LOG COMMENT IN HISTORY
            IncidentHistory.objects.create(
                incident=incident,
                action=action,
                description=f"Commentaire {'ajouté' if action == 'comment_added' else 'modifié'}: {comment[:100]}...",
                temperature=incident.temperature,
                humidity=incident.humidity,
                counter_value=incident.counter
            )

            return JsonResponse({
                "message": "Commentaire soumis avec succès"
            }, status=200)

        except Incident.DoesNotExist:
            return JsonResponse({"error": "Incident non trouvé"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON invalide"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Méthode non autorisée"}, status=405)


@api_view(['GET'])
def temperature_history(request):
    """
    Return temperature history from Dht11 model
    Default: last 7 days
    Query params: start_date, end_date (format: YYYY-MM-DD)
    """
    try:
        # Get date parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Default to last 7 days if no dates provided
        if not start_date or not end_date:
            end_date_obj = timezone.now()
            start_date_obj = end_date_obj - timedelta(days=7)
        else:
            # Parse provided dates
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # Make them timezone aware
            start_date_obj = timezone.make_aware(start_date_obj)
            end_date_obj = timezone.make_aware(end_date_obj.replace(hour=23, minute=59, second=59))

        # Filter measurements by date range
        measurements = Dht11.objects.filter(
            dt__gte=start_date_obj,
            dt__lte=end_date_obj
        ).order_by('dt')

        data = []
        for m in measurements:
            if m.temp is not None:  # Skip null values
                data.append({
                    'timestamp': m.dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'temperature': m.temp,
                })

        return JsonResponse({
            'success': True,
            'data': data,
            'start_date': start_date_obj.strftime('%Y-%m-%d'),
            'end_date': end_date_obj.strftime('%Y-%m-%d'),
            'count': len(data)
        })
    except Exception as e:
        print(f"Error in temperature_history: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@api_view(['GET'])
def humidity_history(request):
    """
    Return humidity history from Dht11 model
    Default: last 7 days
    Query params: start_date, end_date (format: YYYY-MM-DD)
    """
    try:
        # Get date parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Default to last 7 days if no dates provided
        if not start_date or not end_date:
            end_date_obj = timezone.now()
            start_date_obj = end_date_obj - timedelta(days=7)
        else:
            # Parse provided dates
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            # Make them timezone aware
            start_date_obj = timezone.make_aware(start_date_obj)
            end_date_obj = timezone.make_aware(end_date_obj.replace(hour=23, minute=59, second=59))

        # Filter measurements by date range
        measurements = Dht11.objects.filter(
            dt__gte=start_date_obj,
            dt__lte=end_date_obj
        ).order_by('dt')

        data = []
        for m in measurements:
            if m.hum is not None:  # Skip null values
                data.append({
                    'timestamp': m.dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'humidity': m.hum,
                })

        return JsonResponse({
            'success': True,
            'data': data,
            'start_date': start_date_obj.strftime('%Y-%m-%d'),
            'end_date': end_date_obj.strftime('%Y-%m-%d'),
            'count': len(data)
        })
    except Exception as e:
        print(f"Error in humidity_history: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)