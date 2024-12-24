import logging
import json
import base64
import requests

from datetime import datetime, timedelta
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from mixpanel import Mixpanel
from rest_framework import generics, status
from rest_framework.response import Response

from users.permissions import IsRegistered
from reviews.serializers import ReviewListSerializer
from reviews.models import Review

from .serializers import TrackEventSerializer 
    
from django.conf import settings
from django.utils import timezone 
#from django.core.cache import cache

logger = logging.getLogger(__name__)

try:
    mp = Mixpanel(settings.MIXPANEL_API_TOKEN)
except Exception as e:
    logger.error('Error initializing Mixpanel: %s', e)
    mp = None

class TrackEventView(generics.GenericAPIView):
    serializer_class = TrackEventSerializer
    permission_classes = ()
    
    def post(self, request):
        if mp is None:
            return Response({"error": "Mixpanel not initialized"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            event_name = serializer.validated_data['event_name']
            properties = serializer.validated_data.get('properties', {})
            distinct_id = serializer.validated_data.get('distinct_id', 'anonymous')
            
            mp.track(distinct_id, event_name, properties)
            
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Error tracking event: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InitialTackDashBoardView(generics.GenericAPIView):
    permission_classes = [IsRegistered]
    
    def get(self, request):
        try:
            user = request.user
            startup = user.get_startup()

            if not startup:
                return Response({"error": "Startup does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            startupId = startup.id
            startup_id_str = str(startupId)
              
            events = self._fetch_events(startup_id_str)
            main_values = self._get_main_values(events)
            recent_activity = self._get_recent_activity(events, startupId)
            counts_by_day = self._get_event_counts_by_day(events)
            counts_by_month = self._get_event_counts_by_month(events)
            counts_by_six_month = self._get_event_counts_by_six_month(events)
            counts_by_year = self._get_event_counts_by_year(events)
            all_vistors = self._group_events_by_email(events, startupId)

            data = {
                'initialDashBoard':{
                    'totalVisitor': main_values['Visit_Startup_Page'],
                    'pitchViews': main_values['Click_Pitch_Deck'],
                    'videoViews': main_values['Click_Video'],
                    'totalShare': main_values['Total_Shares'],
                    'recentActivity': recent_activity,
                    'pageVisit': {
                        'lastWeek':counts_by_day['Visit_Startup_Page'],
                        'lastMonth':counts_by_month['Visit_Startup_Page'],
                        'lastSixMonth':counts_by_six_month['Visit_Startup_Page'],
                        'lastYear':counts_by_year['Visit_Startup_Page'],
                        },
                    'pitchDeckView':{
                        'lastWeek':counts_by_day['Click_Pitch_Deck'],
                        'lastMonth':counts_by_month['Click_Pitch_Deck'],
                        'lastSixMonth':counts_by_six_month['Click_Pitch_Deck'],
                        'lastYear':counts_by_year['Click_Pitch_Deck'],
                        },
                    'totalShares':{
                        'lastWeek':counts_by_day['Total_Shares'],
                        'lastMonth':counts_by_month['Total_Shares'],
                        'lastSixMonth':counts_by_six_month['Total_Shares'],
                        'lastYear':counts_by_year['Total_Shares'],
                        },
                    'videoView':{
                        'lastWeek':counts_by_day['Click_Video'],
                        'lastMonth':counts_by_month['Click_Video'],
                        'lastSixMonth':counts_by_six_month['Click_Video'],
                        'lastYear':counts_by_year['Click_Video'],
                    },
                },
                'reviewsDashBoard':all_vistors
            }
            
            return Response(data=data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error('Server error: %s', e)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _fetch_events(self, startupId):
        api_secret = settings.MIXPANEL_API_SECRET
        url = 'https://data.mixpanel.com/api/2.0/export/'

        to_date = timezone.now()
        from_date = to_date - timedelta(days=365)

        from_date_str = from_date.strftime("%Y-%m-%d")
        to_date_str = to_date.strftime("%Y-%m-%d")
        where_clause = f'properties["startup_id"] == "{startupId}"'

        params = {
            'from_date': from_date_str, 
            'to_date': to_date_str,   
            'event': '["Visit_Startup_Page", "Click_Pitch_Deck", "Click_Video", "Deck_Download", "Click_Pass_Startup_Button", "Click_Connect_Startup_Button", "Total_Shares"]',
            'where': where_clause
        }
        
        headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic " + base64.b64encode(f"{api_secret}:".encode()).decode(),
        }

        events_response = []
        
        """
        cache_key = f'dashboard_data_{startupId}' 
        cached_data = cache.get(cache_key)
        
        if cached_data:
            
            return cached_data
        else:
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 200 and response.text.strip():
                events_response = [json.loads(line) for line in response.text.strip().split('\n')]
                cache.set(cache_key, events_response, timeout=10800)
            
            return events_response
        """
        response = requests.get(url, params=params, headers=headers)
            
        if response.status_code == 200 and response.text.strip():
            events_response = [json.loads(line) for line in response.text.strip().split('\n')]
            
        return events_response
        
    def _get_main_values(self, events):
        now = datetime.now()
        last_24_hours = now - timedelta(days=1)

        counts = {event: {"total": 0, "last_24_hours": 0} for event in ["Visit_Startup_Page", "Click_Pitch_Deck", "Click_Video", "Total_Shares"]}

        for event in events:
            event_name = event['event']
            event_time = datetime.fromtimestamp(event['properties']['time'])
            if event_name in counts:
                counts[event_name]["total"] += 1
                if event_time > last_24_hours:
                    counts[event_name]["last_24_hours"] += 1

        return counts

    def _get_recent_activity(self, events, startupId):
        email_counts = {}
        now = datetime.now()

        reviews = Review.objects.filter(startup_id=startupId)
        review_map = {review.email: review for review in reviews}

        for event in events:
            properties = event.get('properties', {})
            email = properties.get('email_as_user_id')
            event_time = datetime.fromtimestamp(properties['time'])
            
            if email:
                if email not in email_counts:
                    email_counts[email] = {"count": 0, "last_event_time": event_time}
                
                email_counts[email]["count"] += 1
                if event_time > email_counts[email]["last_event_time"]:
                    email_counts[email]["last_event_time"] = event_time

        email_list = []

        for email, info in email_counts.items():
            time_since_last_event = (now - info["last_event_time"]).total_seconds()
            email_value = email
            
            review = review_map.get(email)
            if review and review.is_anonymous:
                email_value = 'anonymous'
            
            email_list.append({
                "email": email_value,
                "totalVisits": info["count"],
                "lastVisit": time_since_last_event
            })
        
        
        email_list_sorted = sorted(email_list, key=lambda x: x["lastVisit"])
        
        return email_list_sorted[:4]

    def _get_event_counts_by_day(self, events):
        now = datetime.now()
        last_7_days = now - timedelta(days=7)

        counts_total = {event: 0 for event in ["Visit_Startup_Page", "Click_Pitch_Deck", "Click_Video", "Total_Shares"]}
        counts_by_day = {event: defaultdict(int) for event in ["Visit_Startup_Page", "Click_Pitch_Deck", "Click_Video", "Total_Shares"]}

        for event in events:
            event_name = event['event']
            event_time = datetime.fromtimestamp(event['properties']['time'])
            event_day = event_time.strftime("%Y-%m-%d")

            if event_name in counts_total:
                counts_total[event_name] += 1
                if event_time > last_7_days:
                    counts_by_day[event_name][event_day] += 1
        
        days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        days.reverse()
        result = {
            event: {
                "total": counts_total[event],
                "days":[{"date": day, "qty": counts_by_day[event].get(day, 0)} for day in days]
            } for event in counts_total
        }

        return result
    
    def _get_event_counts_by_month(self, events):
        now = datetime.now()
        last_30_days = now - timedelta(days=30)

        tracked_events = ["Visit_Startup_Page", "Click_Pitch_Deck", "Click_Video", "Total_Shares"]
        
        counts_total = {event: 0 for event in tracked_events}
        counts_by_day = {event: defaultdict(int) for event in tracked_events}

        for event in events:
            event_name = event['event']
            if event_name not in tracked_events:
                continue
            event_time = datetime.fromtimestamp(event['properties']['time'])
            event_day = event_time.strftime("%Y-%m-%d")

            counts_total[event_name] += 1
            if event_time > last_30_days:
                counts_by_day[event_name][event_day] += 1
        
        days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        days.reverse()
        result = {
            event: {
                "total": counts_total[event],
                "days": [{"date": day, "qty": counts_by_day[event].get(day, 0)} for day in days]
            } for event in counts_total
        }

        return result
        
    def _get_event_counts_by_six_month(self, events):
        now = datetime.now()
        start_date = now - relativedelta(months=6)

        tracked_events = ["Visit_Startup_Page", "Click_Pitch_Deck", "Click_Video", "Total_Shares"]

        counts_total = {event: 0 for event in tracked_events}
        counts_by_month = {event: defaultdict(int) for event in tracked_events}

        for event in events:
            event_name = event['event']
            if event_name not in tracked_events:
                continue  

            event_time = datetime.fromtimestamp(event['properties']['time'])
            event_month = event_time.strftime("%Y-%m")

            counts_total[event_name] += 1
            if event_time >= start_date:
                counts_by_month[event_name][event_month] += 1
        
        
        months = [(now - relativedelta(months=i)).strftime("%Y-%m") for i in range(6)]
        months.reverse()

        result = {
            event: {
                "total": counts_total[event],
                "months": [{"date": month, "qty": counts_by_month[event].get(month, 0)} for month in months]
            } for event in counts_total
        }

        return result
    
    def _get_event_counts_by_year(self, events):
        now = datetime.now()
        start_date = now - relativedelta(years=1)

        tracked_events = ["Visit_Startup_Page", "Click_Pitch_Deck", "Click_Video", "Total_Shares"]

        counts_total = {event: 0 for event in tracked_events}
        counts_by_month = {event: defaultdict(int) for event in tracked_events}

        for event in events:
            event_name = event['event']
            if event_name not in tracked_events:
                continue 

            event_time = datetime.fromtimestamp(event['properties']['time'])
            event_month = event_time.strftime("%Y-%m")

            counts_total[event_name] += 1
            if event_time >= start_date:
                counts_by_month[event_name][event_month] += 1

    
        months = [(now - relativedelta(months=i)).strftime("%Y-%m") for i in range(12)]
        months.reverse()

        result = {
            event: {
                "total": counts_total[event],
                "months": [{"date": month, "qty": counts_by_month[event].get(month, 0)} for month in months]
            } for event in counts_total
        }

        return result
    
    def _group_events_by_email(self, events, startupId):
        email_counts = {}

        for event in events:
            email = event['properties'].get('email_as_user_id')
            event_name = event['event']
            event_time = datetime.fromtimestamp(event['properties']['time'])
            props = event['properties']

            if email:
                if email not in email_counts:
                    email_counts[email] = {
                        "totalVisits": 0,
                        "totalTimeSpentOnPages": 0,
                        "lastEventTime": event_time,
                        "userBrowser": None,
                        "userDeviceType": None,
                        "userOs": None,
                        "latestPitchDeck": {
                            "numberSlidesViewed": None,
                            "timeSpentPerSlide": None,
                            "totalTime": None
                        },
                        "latestVideo": {
                            "totalTimeSpentOnVideo": None,
                            "finishedVideo": None
                        },
                        "latestDeckDownload": {
                            "deckDownloadYes": None
                        },
                        "latestPassButton": {
                            "passYes": None
                        },
                        "latestConnectButton": {
                            "connectYes": None
                        },
                        "totalShares": 0
                    }

                email_counts[email]["totalVisits"] += 1

                if event_name == "Visit_Startup_Page":
                    time_spent_on_page = props.get("time_spent_on_page")
                    if isinstance(time_spent_on_page, (int, float)):
                        email_counts[email]["totalTimeSpentOnPages"] += time_spent_on_page
                    elif isinstance(time_spent_on_page, str) and time_spent_on_page.isdigit():
                        email_counts[email]["totalTimeSpentOnPages"] += int(time_spent_on_page)
                    
                    if event_time >= email_counts[email]["lastEventTime"]:
                        email_counts[email]["userBrowser"] = props.get("user_browser")
                        email_counts[email]["userDeviceType"] = props.get("user_device_type")
                        email_counts[email]["userOs"] = props.get("user_os")

                if event_name == "Click_Pitch_Deck" and event_time >= email_counts[email]["lastEventTime"]:
                    raw_time_spent = props.get("time_spent_per_slide", {})
                    formatted_time_spent = [{"slide": int(slide), "time": time} for slide, time in raw_time_spent.items()]
                    totalTime = props.get("total_time", 0)
                    email_counts[email]["latestPitchDeck"] = {
                        "numberSlidesViewed": props.get("number_slides_viewed"),
                        "timeSpentPerSlide": formatted_time_spent,
                        "totalTime": totalTime
                    }

                if event_name == "Click_Video" and event_time >= email_counts[email]["lastEventTime"]:
                    email_counts[email]["latestVideo"] = {
                        "totalTimeSpentOnVideo": props.get("total_time_spent_on_video"),
                        "finishedVideo": props.get("finished_video")
                    }

                if event_name == "Deck_Download" and event_time >= email_counts[email]["lastEventTime"]:
                    email_counts[email]["latestDeckDownload"] = {
                        "deckDownloadYes": props.get("deck_download_yes")
                    }

                if event_name == "Click_Pass_Startup_Button" and event_time >= email_counts[email]["lastEventTime"]:
                    email_counts[email]["latestPassButton"] = {
                        "passYes": props.get("pass_yes")
                    }

                if event_name == "Click_Connect_Startup_Button" and event_time >= email_counts[email]["lastEventTime"]:
                    email_counts[email]["latestConnectButton"] = {
                        "connectYes": props.get("connect_yes")
                    }

                if event_name == "Total_Shares":
                    total_shares = props.get("count", 1) 
                    if isinstance(total_shares, (int, float)):
                        email_counts[email]["totalShares"] += total_shares
                    elif isinstance(total_shares, str) and total_shares.isdigit():
                        email_counts[email]["totalShares"] += int(total_shares)

                if event_time > email_counts[email]["lastEventTime"]:
                    email_counts[email]["lastEventTime"] = event_time

        now = datetime.now()
        email_list = []

        for email, info in email_counts.items():
            time_since_last_event = (now - info.pop("lastEventTime")).total_seconds()
            info["lastVisit"] = time_since_last_event
            review = Review.objects.filter(startup_id=startupId,email=email).first()
            deview_data = ReviewListSerializer(review).data
            email_value = email
            if review and review.is_anonymous:
                email_value = 'anonymous'
            email_list.append({"email": email_value,"review":deview_data ,**info})

        return email_list