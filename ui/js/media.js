// Copyright (c) 2025 b1on1cdog
// Licensed under the MIT License

let videoTimeUpdateIntervalId;
let videoTimeDisplayTimeoutId;
let videos = { };

function find_videoId(video_url){
  const videoId = Object.keys(videos).find(
    key => videos[key].url === video_url
  );
  return videoId;
}

function playVideo(videoId, startDuration = 0){
  isVideoPlayer = true;
  video = document.getElementById("videoPlayer");
  video.classList.add("active");

/*
  var source = document.createElement('source');
  source.setAttribute('src', videoFile);
  source.setAttribute('type', 'video/mp4');
  video.appendChild(source);
*/
  videoId = videoId.replace("video_", "");
  videoFile = videos[videoId].url;
  video.dataset.video_id = videoId;
  video.src = videoFile;
  video.load();
  video.play();
  hideUI(true);
  if (isContextMenu) {
    closeCTX();
  }
  videoTime = document.getElementById("videoTime");
  videoTimeUpdateIntervalId = setInterval(() => {
    if (videoTime == undefined) {
      videoTime = document.getElementById("videoTime");
    }
    videoTime.innerText = formatDuration(video.currentTime) + "/" + formatDuration(video.duration);
  }, "1000");
  video.currentTime = startDuration;
}

function closeVideo(){
  isVideoPlayer = false;
  video = document.getElementById("videoPlayer");
  video.classList.remove("active");
  video.pause();
  /*
  we need to register the time before closing the video
  To-do: make sure we are using right video (ex: PlayVideo remote command bypasses currentMedia)
  */
  if ("video_id" in video.dataset && video.currentTime > 30){
    video_id = video.dataset.video_id;
    backend_log(video_id);
    videos[video_id]["resume"] = video.currentTime;
    document.getElementById("video_"+video_id).dataset.resume = video.currentTime
    send_videos_metadata(videos);
  }
  
  video.currentTime = 0;
  hideUI(false);
  if (videoTimeUpdateIntervalId != undefined){
    clearInterval(videoTimeUpdateIntervalId);
    document.getElementById("videoTime").classList.remove("active");
  }
}

// video_parser.js
function formatDuration(totalSeconds) {
  const sec = Math.floor(totalSeconds % 60).toString().padStart(2, '0');
  const min = Math.floor((totalSeconds / 60) % 60).toString().padStart(2, '0');
  const hrs = Math.floor(totalSeconds / 3600);

  return hrs > 0 ? `${hrs}:${min}:${sec}` : `${min}:${sec}`;
}

function videoControl(action){
  video = document.getElementById("videoPlayer");
  switch (action) {
    case "left":
      video.currentTime = Math.max(video.currentTime - 15, 0);
      break;
    case "right":
      video.currentTime = Math.min(video.currentTime + 15, video.duration);
      break;
    case "up":
      video.volume = Math.min(video.volume + 0.05, 1);
      break;
    case "down":
      video.volume = Math.max(video.volume - 0.05, 0);
      break;
    case "back":
      closeVideo();
      return;
    case "confirm":
      if (video.paused) {
        video.play();
      } else {
        video.pause();
      }
      break;
    case "options":
      playSound("shot");
      take_video_screenshot();
      break;
    default:
      break;
  }
  videoTime = document.getElementById("videoTime");
  videoTime.innerText =  formatDuration(video.currentTime) + "/" + formatDuration(video.duration);
  videoTime.classList.add("active");
  if (videoTimeDisplayTimeoutId != undefined) {
    clearTimeout(videoTimeDisplayTimeoutId);
  }
  videoTimeDisplayTimeoutId = setTimeout(() => {
      videoTime.classList.remove("active");
    }, "3500");
}


function send_videos_metadata(){
    fetch("/video/set", {
      method: "POST",
      body: JSON.stringify(videos),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
      }).then((response) => {
        
      });
}
function deleteVideo(videoItem){
    const videoFile = videoItem.dataset.play;
    fetch(videoFile, {
      method: "DELETE",
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
      }).then((response) => {
        videoItem.remove();
        document.getElementById("videoContextMenu").classList.remove("active");
        isContextMenu = false;
        mediaItems = document.querySelectorAll('.videoLauncher')
        if (mediaItems.length == 0) {
          goHome();
        } else {
          currentMedia--;
          mediaItems[currentMedia].focus();
        }
      });
}

function send_video_thumbnail(thumbnail, video_id){
    fetch("/video/thumbnail/"+video_id, {
      method: "POST",
      body: JSON.stringify(thumbnail),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
      }).then((response) => {
        
      });
}

function draw_video_png(vid){
    const c  = document.createElement('canvas');
    c.width  = vid.videoWidth;
    c.height = vid.videoHeight;
    c.getContext('2d').drawImage(vid, 0, 0);
    const png = c.toDataURL('image/png');
    return png;
}


function simulateScreenshotEffect(vid) {
  vid.classList.add("screenshot-bounce");

  const flash = document.getElementById("flash");
  flash.classList.add("active");

  setTimeout(() => {
    vid.classList.remove("screenshot-bounce");
    flash.classList.remove("active");
  }, 100);
}

function take_video_screenshot(){
    vid = document.getElementById("videoPlayer");
    screenshot = draw_video_png(vid);
    simulateScreenshotEffect(vid);
    fetch("/video/screenshot/", {
      method: "POST",
      body: JSON.stringify(screenshot),
      headers: {
        "Content-type": "application/json; charset=UTF-8"
      }
      }).then((response) => {
        
      });
}

async function get_video_metadata(video_url, vid){
    console.log("processing metadata for " + video_url);
    vid.id = 'metadata-video';
    vid.preload = 'metadata';
    vid.src = video_url;
    vid.muted = true;
    document.body.appendChild(vid);

    await new Promise(r => vid.onloadedmetadata = r);
    const duration = vid.duration;

    vid.currentTime = Math.min(90.5, duration / 2);

    await new Promise(r => vid.onseeked = r);

    png = draw_video_png(vid);

    vid.pause();
    metadata = {
        "duration" : vid.duration,
        "thumbnail" : png,
    }
    return metadata;
}

function refreshVideoMetadata(video_id, video_duration = "00:00"){
    videoElement = document.getElementById("video_"+video_id);
    if (videoElement != undefined){
        try {
            th = videoElement.getElementsByClassName("video-thumbnail")[0];
            th.src = th.src;
            duration = videoElement.getElementsByClassName("duration")[0];
            duration.textContent = formatDuration(video_duration);
        } catch {}
    }
}

async function update_videos_metadata(vids){
    const vid = document.createElement('video');
    for (const id in vids) {
        const video = vids[id];
        if ("duration" in video && video["thumbnail_exists"]){
            //console.log("skipping "+id)
            continue;
        }
        const metadata = await get_video_metadata(video.url, vid);
        thumbnail = metadata["thumbnail"];
        delete metadata.thumbnail;
        Object.assign(videos[id], metadata);
        send_video_thumbnail(thumbnail, id);

        //let's refresh thumbnail
        setTimeout(() => {
            refreshVideoMetadata(id, metadata.duration);
        }, "500");
    }
  //  console.log(JSON.stringify(videos));
    send_videos_metadata();
    vid.remove();
}

  async function fetch_videos(autoplay_video = ""){
        document.querySelectorAll('.videoLauncher').forEach(el => el.remove());
        response = await fetch("/media/get");
        if (!response.ok) {
            throw new Error(`HTTP ${network_resp.status}`);
        }
        data = await response.json();
        videos = data["videos"];
  
        update_videos_metadata(videos);
        mediaList = document.getElementsByClassName("mediaList")[0];
        for (const id in videos){
            video = videos[id];
            
            const videoLauncher = document.createElement('button');
            videoLauncher.className = 'videoLauncher';
            /*
            if (favoriteGames.has(AppID)){
                app.classList.add("favorite");
            }*/
            videoLauncher.id = "video_" + id;
            videoLauncher.dataset.play = video.url;
            if ("resume" in video) {
              videoLauncher.dataset.resume = video.resume;
            }
            const videoTitle = document.createElement('div');
            videoTitle.className = "video-title";
            videoTitle.textContent = video.file
            videoTitle.dataset.text = videoTitle.textContent;
            const videoImage = document.createElement('img');
            videoImage.className = 'video-thumbnail';
            videoImage.src = video.thumbnail_url;
            videoImage.alt = video.file;
            const durationElement = document.createElement('div');
            durationElement.className = "duration";
            durationElement.textContent = formatDuration(video.duration);
            videoLauncher.appendChild(videoTitle);
            videoLauncher.appendChild(videoImage);
            videoLauncher.appendChild(durationElement);
            mediaList.appendChild(videoLauncher);
            videoLauncher.addEventListener('focus', () => {
              videoLauncher.scrollIntoView({ behavior: "instant", block: "center" });
            });
        }
        if (autoplay_video != ""){
          videoUri = encodeURI(autoplay_video);
          backend_log("trying to find videoId for "+videoUri)
          videoId = find_videoId(videoUri);
          if (videoId == undefined) {
            backend_log("Unable to autoplay media")
          } else {
            playVideo(videoId);
          }
          
        }
}