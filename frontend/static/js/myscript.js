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
    copyToClipboard(url);
    window.open("", '_blank');
    
}
