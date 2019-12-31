def get_youtube_streaming_data (api_key="AIzaSyDoxv6yPVLKSMJwXVF0-HKnkdl0DcgE8Ak",playlist_id="PLU12uITxBEPGpEPrYAxJvNDP6Ugx2jmUx"):
    '''
     유튜브 실시간 방송의 세부 데이터를 얻기 위한 시청자 수 기준 상위 100개의 방송 고유 아이디 수집
     api_key : 유튜브 API 사용을 위해 발급받은 키값 -> 작동이 안되면 가장 먼저 체크(api키 교체)
     playlist_id : 유튜브 실시간 탭에서 실시간 시청자 수 기준 상위 100개의 방송이 담긴 플레이리스트 
    '''
    from bs4 import BeautifulSoup
    from urllib.request import urlopen
    import requests, json
    import pandas as pd
    from datetime import datetime,timedelta
    
    page_token = ""
    live_video_id = []    
    while True:
        
        target_url = "https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={}&pageToken={}&maxResults=50&key={}".format(playlist_id, page_token, api_key)
        html = requests.get (target_url)

        soup = BeautifulSoup (html.text, "html.parser" )
        soup = eval(soup.text.replace("false","False").replace("true","True"))
    
        if 'error' in soup:
            return "api limit 초과. 잠시 후 다시 시도하세요."
        
        for n in range(len(soup["items"])):
            live_video_id.append(soup["items"][n]["snippet"]["resourceId"]["videoId"])      
                
        if 'nextPageToken' in soup:
            page_token = soup["nextPageToken"] 
        else:
            break    
            
    #########################################################################
    # api를 통해 얻은 비디오 고유값 100개(live_video_id)로 실시간 스트리밍 세부 정보 얻기 (불필요한 데이터가 있다면 임의로 수정)
    title = [] # 방송 제목
    channel_name = [] # 채널 이름
    category = [] # 방송 카테고리
    tags = [] # 방송에 설정한 태그 (설정하지 않을 수 있음)
    start_time = [] # 방송 시작 시간
    current_viewer = [] # 수집 당시 시청자 수
    view_count = [] # 누적 시청자 수
    likes = [] # 좋아요 수 (비공개 가능)
    dislikes = [] # 싫어요 수  (비공개 가능)
    
    for video_id in live_video_id:
        # 방송제목, 채널이름, 태그, 카테고리 불러오기 
        target= "https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key=AIzaSyDoxv6yPVLKSMJwXVF0-HKnkdl0DcgE8Ak".format(video_id)
        html = requests.get(target)
        soup = BeautifulSoup (html.text, "html.parser" )
        # soup = eval(soup.text.replace("false","False").replace("true","True"))
        soup = eval(soup.text.replace("false","False").replace("true","True"))

        # 비공개 스트리밍이면 데이터를 수집할 수 없음
        if not soup["items"]:
            print("https://www.youtube.com/watch?v={}는 비공개 동영상입니다.".format(video_id))
            continue

        title.append(soup["items"][0]["snippet"]["title"])
        channel_name.append(soup["items"][0]["snippet"]["channelTitle"])
        # 카테고리 딕셔너리
        category_dict = {'1': '영화/애니메이션', '2': '자동차', '10': '음악', '15': '동물', '17': '스포츠', '18': '단편 영화',
        '19': '여행/이벤트', '20': '게임', '21': '브이로그', '22': '인물/블로그', '23': '코미디', '24': '엔터테인먼트',
        '25': '뉴스/정치', '26': '노하우/스타일', '27': '교육', '28': '과학기술', '29' : '비영리/사회운동', '30': '영화', 
        '31': '애니메/애니메이션','32': '액션/모험', '33': '고전', '34': '코미디', '35': '다큐멘터리', '36': '드라마',
        '37': '가족', '38': '외국','39': '공포', '40': '공상과학/판타지', '41': '스릴러', '42': '단편', '43': '프로그램',
        '44': '예고편'}
        category.append(category_dict[soup["items"][0]["snippet"]["categoryId"]])

        # 방송에 지정한 태그가 없다면 데이터는 "-"로 추가됨
        if "tags" in soup["items"][0]["snippet"]: 
            tags.append(soup["items"][0]["snippet"]["tags"])
        else:
            tags.append("-")

        #########################################################################
        # 현재시청자 수, 라이브 시작시간을 불러오기 위한 liveStreamingDetails api 사용
        target= "https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id={}&key=AIzaSyDoxv6yPVLKSMJwXVF0-HKnkdl0DcgE8Ak".format(video_id)
        html = requests.get(target)
        soup = BeautifulSoup (html.text, "html.parser" )
        # soup = eval(soup.text.replace("false","False").replace("true","True"))
        soup = eval(soup.text.replace("false","False").replace("true","True"))


        # 시작시간 (api 시차 보정)
        stime = soup["items"][0]["liveStreamingDetails"]["actualStartTime"].replace("T"," ")[:-5]
        stime = datetime.strptime(stime, '%Y-%m-%d %H:%M:%S') + timedelta(hours=9)
        start_time.append(datetime.strftime(stime,"%Y-%m-%d %H:%M:%S"))

        # 수집 당시 시청자수 
        # 데이터 수집 중 방송이 끝나 현재 시청자 수를 가져올 수 없다면 해당 데이터는 "finished"로 추가됨
        if not "concurrentViewers" in soup["items"][0]["liveStreamingDetails"] :
            current_viewer.append("finished")
        else: 
            current_viewer.append(soup["items"][0]["liveStreamingDetails"]["concurrentViewers"])    
       #########################################################################
       # 누적시청자 수, 좋아요/싫어요 수를 불러오기 위한 statistics api 사용
        target= "https://www.googleapis.com/youtube/v3/videos?part=statistics&id={}&key=AIzaSyDoxv6yPVLKSMJwXVF0-HKnkdl0DcgE8Ak".format(video_id)
        html = requests.get(target)
        soup = BeautifulSoup (html.text, "html.parser" )
        # soup = eval(soup.text.replace("false","False").replace("true","True"))
        soup = eval(soup.text.replace("false","False").replace("true","True"))    

        view_count.append(soup["items"][0]["statistics"]["viewCount"])   

        # '좋아요/싫어요' 수를 공개하지 않았다면 해당 데이터는 "-"로 추가됨
        if "likeCount" and "dislikeCount" in soup["items"][0]["statistics"]:
            likes.append(soup["items"][0]["statistics"]["likeCount"])
            dislikes.append(soup["items"][0]["statistics"]["dislikeCount"])
        else:
            likes.append("-")
            dislikes.append("-")
        
    #########################################################################
    # 수집한 데이터를 데이터프래임으로 만들기 (불필요한 데이터가 있다면 임의로 수정할 것)
    youtube_data = pd.DataFrame()
    youtube_data["title"]=title
    youtube_data["channel_name"]=channel_name
    youtube_data["category"]=category
    youtube_data["tags"]=tags
    youtube_data["start_time"]=start_time
    youtube_data["current_viewer"]=current_viewer
    youtube_data["view_count"]=view_count
    youtube_data["likes"]=likes
    youtube_data["dislikes"]=dislikes
        
    return youtube_data

