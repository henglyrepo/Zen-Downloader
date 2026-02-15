let currentVideoInfo = null;
let selectedFormat = 'best';
let currentTaskId = null;
let eventSource = null;

async function getVideoInfo() {
    const url = document.getElementById('urlInput').value.trim();
    const errorMsg = document.getElementById('errorMsg');
    const loading = document.getElementById('loading');
    const videoSection = document.getElementById('videoSection');
    
    errorMsg.classList.add('hidden');
    
    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }
    
    loading.classList.remove('hidden');
    videoSection.classList.add('hidden');
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000);
        
        const response = await fetch('/api/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        currentVideoInfo = data;
        
        if (data.type === 'video') {
            showSingleVideo(data);
        } else if (data.type === 'playlist') {
            showPlaylist(data);
        }
        
        videoSection.classList.remove('hidden');
        
    } catch (err) {
        let errorMessage = 'Failed to fetch video info. Please try again.';
        if (err.name === 'AbortError') {
            errorMessage = 'Request timed out. Please try again.';
        } else if (err.message) {
            errorMessage = err.message;
        }
        showError(errorMessage);
    } finally {
        loading.classList.add('hidden');
    }
}

function showSingleVideo(info) {
    document.getElementById('singleVideo').classList.remove('hidden');
    document.getElementById('playlistSection').classList.add('hidden');
    
    document.getElementById('videoThumbnail').src = info.thumbnail;
    document.getElementById('videoTitle').textContent = info.title;
    document.getElementById('videoDuration').textContent = info.duration;
    document.getElementById('videoUploader').textContent = info.uploader || 'Unknown';
    document.getElementById('videoViews').textContent = info.view_count ? formatNumber(info.view_count) : 'N/A';
    
    const formatList = document.getElementById('formatList');
    formatList.innerHTML = '';
    
    const uniqueFormats = [];
    const seen = new Set();
    
    for (const fmt of info.formats) {
        const label = `${fmt.resolution} (${fmt.ext})`;
        if (!seen.has(label)) {
            seen.add(label);
            uniqueFormats.push({ ...fmt, label });
        }
    }
    
    uniqueFormats.forEach((fmt, idx) => {
        const div = document.createElement('div');
        div.className = `format-option p-3 rounded-lg border border-gray-700 cursor-pointer ${idx === 0 ? 'selected' : ''}`;
        div.dataset.formatId = fmt.format_id;
        
        const size = fmt.filesize ? formatFileSize(fmt.filesize) : 'Unknown';
        div.innerHTML = `
            <div class="font-semibold">${fmt.label}</div>
            <div class="text-xs text-gray-400">${size}</div>
        `;
        
        div.onclick = () => selectFormat(fmt.format_id, div);
        formatList.appendChild(div);
    });
    
    if (uniqueFormats.length > 0) {
        selectedFormat = uniqueFormats[0].format_id;
    }
}

function showPlaylist(info) {
    document.getElementById('singleVideo').classList.add('hidden');
    document.getElementById('playlistSection').classList.remove('hidden');
    
    document.getElementById('playlistTitle').textContent = `${info.title} (${info.videos.length} videos)`;
    
    const videoList = document.getElementById('videoList');
    videoList.innerHTML = '';
    
    info.videos.forEach((video, idx) => {
        const div = document.createElement('div');
        div.className = 'video-card flex items-center gap-4 p-3 glass rounded-xl cursor-pointer';
        div.innerHTML = `
            <img src="${video.thumbnail}" class="w-24 h-14 object-cover rounded" alt="${video.title}">
            <div class="flex-1 min-w-0">
                <div class="font-semibold truncate">${video.title}</div>
                <div class="text-sm text-gray-400">${video.duration}</div>
            </div>
            <i class="fas fa-chevron-right text-gray-500"></i>
        `;
        videoList.appendChild(div);
    });
}

function selectFormat(formatId, element) {
    document.querySelectorAll('.format-option').forEach(el => el.classList.remove('selected'));
    element.classList.add('selected');
    selectedFormat = formatId;
}

async function startDownload() {
    const url = document.getElementById('urlInput').value.trim();
    const audioOnly = document.getElementById('audioOnly').checked;
    
    document.getElementById('inlineProgress').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                url,
                format_id: selectedFormat,
                audio_only: audioOnly
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            document.getElementById('inlineProgress').classList.add('hidden');
            return;
        }
        
        currentTaskId = data.task_id;
        
        startProgressTracking(data.task_id);
        
    } catch (err) {
        showError('Failed to start download');
        document.getElementById('inlineProgress').classList.add('hidden');
    }
}

function startProgressTracking(taskId) {
    eventSource = new EventSource(`/api/progress/${taskId}`);
    
    eventSource.onmessage = function(event) {
        const progress = JSON.parse(event.data);
        
        if (progress.status === 'completed') {
            eventSource.close();
            document.getElementById('inlineProgress').classList.add('hidden');
            document.getElementById('progressBar').style.width = '0%';
            document.getElementById('progressPercent').textContent = '0%';
            document.getElementById('progressSpeed').textContent = '';
            
            // Download file without redirect
            const filename = progress.filename || 'download.mp4';
            fetch(`/download/${currentTaskId}`)
                .then(response => {
                    if (!response.ok) throw new Error('Download failed');
                    return response.blob();
                })
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    resetApp();
                })
                .catch(err => {
                    console.error('Download error:', err);
                    resetApp();
                });
        } else if (progress.status === 'error') {
            eventSource.close();
            document.getElementById('inlineProgress').classList.add('hidden');
            showError(progress.error || 'Download failed');
        } else if (progress.progress !== undefined) {
            updateProgressBar(progress.progress, progress.speed);
        }
    };
}

function updateProgressBar(percent, speed) {
    document.getElementById('progressBar').style.width = percent + '%';
    document.getElementById('progressPercent').textContent = percent + '%';
    
    if (speed) {
        document.getElementById('progressSpeed').textContent = speed;
    }
}

function showError(message) {
    const errorMsg = document.getElementById('errorMsg');
    errorMsg.textContent = message;
    errorMsg.classList.remove('hidden');
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('inlineProgress').classList.add('hidden');
}

async function resetApp() {
    if (currentTaskId) {
        try {
            await fetch(`/api/cleanup/${currentTaskId}`, { method: 'POST' });
        } catch (e) {}
    }
    
    if (eventSource) {
        eventSource.close();
    }
    
    currentVideoInfo = null;
    selectedFormat = 'best';
    currentTaskId = null;
    eventSource = null;
    
    document.getElementById('urlInput').value = '';
    document.getElementById('audioOnly').checked = false;
    document.getElementById('errorMsg').classList.add('hidden');
    document.getElementById('videoSection').classList.add('hidden');
    document.getElementById('downloadSection').classList.add('hidden');
    document.getElementById('inlineProgress').classList.add('hidden');
    document.getElementById('progressBar').style.width = '0%';
}

function formatNumber(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
}

function formatFileSize(bytes) {
    if (!bytes) return 'Unknown';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
}

document.getElementById('urlInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        getVideoInfo();
    }
});
