// 预览视频窗口
function openPrevModal(videoSrc) {
    document.getElementById('videoSource').src = videoSrc;
    document.getElementById('videoPlayer').load();
    document.getElementById('videoPlayer').volume = 0.1;
    document.getElementById('prevModal').style.display = "block";
}

function closePrevModal() {
    document.getElementById('prevModal').style.display = "none";
    document.getElementById('videoPlayer').pause();
}

function markAsDeleted(movieId) {
    fetch(`/mark_as_deleted/${movieId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({ 'id': movieId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Movie marked as deleted.');
            location.reload();
        } else {
            alert('Failed to mark movie as deleted.');
        }
    });
}

function unsecuredCopyToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
    } catch (err) {
      console.error('Unable to copy to clipboard', err);
    }
    document.body.removeChild(textArea);
}


// 复制到剪切板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {

    }, function(err) {
        alert('无法复制路径: ', err);
    });

}

// 更新评分
function rateMovie(movieId) {
    var ratingInput = document.getElementById('rating-' + movieId);
    var rating = parseFloat(ratingInput.value);
    if (isNaN(rating) || rating < 0 || rating > 5) {
        alert('请输入有效的评分 (0-5)');
        return;
    }
    var encodedMovieId = movieId.replace(/\//g, '_');
    fetch(`/movie/rate_movie/${encodedMovieId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({ 'rating': rating })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('评分已提交', 'bg-green-500');
        } else {
            showMessage('评分提交失败', 'bg-red-500');
        }
    });
}

// 打开模态框
function showMessage(message, bgColor) {
    var messageContainer = document.getElementById('messageContainer');
    var messageLabel = document.createElement('div');
    messageLabel.className = `text-white px-4 py-2 rounded ${bgColor}`;
    messageLabel.innerText = message;
    messageContainer.appendChild(messageLabel);

    setTimeout(() => {
        messageContainer.removeChild(messageLabel);
    }, 1000);
}


// 更新评分
function updateComment(movieId) {
    var commentInput = document.getElementById('comment-' + movieId);
    var comment = commentInput.value;
    var encodedMovieId = movieId.replace(/\//g, '_');
    fetch(`/movie/update_comment/${encodedMovieId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({ 'comment': comment })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('评论已更新', 'bg-green-500');
        } else {
            showMessage('评论更新失败', 'bg-red-500');
        }
    });
}


// 关闭模态框
function showMessage(message, bgColor) {
    var messageContainer = document.getElementById('messageContainer');
    var messageLabel = document.createElement('div');
    messageLabel.className = `text-white px-4 py-2 rounded ${bgColor}`;
    messageLabel.innerText = message;
    messageContainer.appendChild(messageLabel);

    setTimeout(() => {
        messageContainer.removeChild(messageLabel);
    }, 1000);
}


// 本地/线上资源切换
function toggleLocalParam() {
    const url = new URL(window.location.href);
    const localParam = url.searchParams.get('local');
    if (localParam === '0') {
        url.searchParams.set('local', '1');
    } else {
        url.searchParams.set('local', '0');
    }
    // window.location.href = url.toString();
    window.location.assign(url.toString());

}

// 鼠标悬浮效果
function zoomIn(event) {
    const img = event.target;
    img.style.transformOrigin = `${event.offsetX}px ${event.offsetY}px`;
    img.style.transform = 'scale(2)';
}

function zoomOut(event) {
    const img = event.target;
    img.style.transform = 'scale(1)';
}

//图片浮窗
function showOriginalImage(imageSrc) {
    document.getElementById('originalImage').src = imageSrc;
    // document.getElementById('videoPlayer').load();
    document.getElementById('imageModal').style.display = "block";
}

function closeImageModal() {
    document.getElementById('imageModal').style.display = "none";
}


// 删除电影
function delMovie(movie_id) {
    fetch(`/movie/del_movie/${movie_id}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({ 'id': movie_id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('已删除', 'bg-green-500');
            location.reload();
        } else {
            showMessage('删除失败', 'bg-red-500');
        }
    });
}

function openUrl(url) {
    unsecuredCopyToClipboard(url);
    // window.open("", '_blank');
    // console.log(url);
    
}

 // 打开磁链浮窗并显示磁链信息

 // 创建用于展示 magnet 的 li 元素
function createMagnetListItem(magnet) {
    const li = document.createElement('li');
    li.className = 'flex justify-between items-center py-2 text-xs';

    const magnetInfo = document.createElement('span');
    magnetInfo.textContent = `${magnet.name} - ${magnet.meta} `;
    li.appendChild(magnetInfo);

    if(`${magnet.tags}`){
        const magnetTag = document.createElement('span');
        magnetTag.textContent = `${magnet.tags}`;
        magnetTag.className = 'bg-green-500 text-white  px-2 py-1 rounded ml-2';
        li.appendChild(magnetTag);
    }
    
    const magnetTime = document.createElement('span');
    magnetTime.textContent = `${magnet.time}`;
    magnetTime.className = 'bg-blue-500 text-white px-2 py-1 rounded ml-2';
    li.appendChild(magnetTime);

    const downloadButton = document.createElement('button');
    downloadButton.textContent = '下载';
    downloadButton.className = 'bg-blue-500 text-white px-2 py-1 rounded ml-2';
    // magnet:?xt=urn:btih:0121bfbfb9a162ad3aac26f4ff42a71570d1ed6e&=[javdb.com]
    safe_id = magnet.id.substring(20,60);
    downloadButton.onclick = () => downloadMagnet(`${safe_id}`);
    li.appendChild(downloadButton);

    return li;
}


function showMagnets(movieId) {
    console.log(movieId);
    fetch(`/movie/magnets/${movieId}/`)
        .then(response => response.json())
        .then(data => {
            const magnetList = document.getElementById('magnetList');
            magnetList.innerHTML = ''; // 清空之前的内容
            data.magnets.forEach(magnet => {
                const li = createMagnetListItem(magnet);
                magnetList.appendChild(li);
            });
            document.getElementById('magnetModal').style.display = "block";
        });
}

// 关闭磁链浮窗
function closeMagnetModal() {
    document.getElementById('magnetModal').style.display = "none";
}

function downloadMagnet(magnetID) {
    console.log(magnetID);
    fetch(`/movie/download/${magnetID}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({ 'id': magnetID })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('已下载', 'bg-green-500');
                location.reload();
            } else {
                showMessage('下载失败', 'bg-red-500');
            }
        });
}