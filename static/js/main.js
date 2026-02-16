let currentVideoInfo = null;
let selectedFormat = 'best';
let currentTaskId = null;
let eventSource = null;
let appSettings = null;

async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        appSettings = await response.json();
        
        const pathSelect = document.getElementById('downloadPath');
        pathSelect.innerHTML = '';
        
        // Add Downloads folder option
        const downloadsOption = document.createElement('option');
        downloadsOption.value = appSettings.download_path;
        downloadsOption.textContent = `📥 Downloads (${appSettings.download_path})`;
        pathSelect.appendChild(downloadsOption);
        
        // Add app folder option
        const appOption = document.createElement('option');
        appOption.value = appSettings.app_download_path;
        appOption.textContent = `📁 App Folder (${appSettings.app_download_path})`;
        appOption.selected = true;
        pathSelect.appendChild(appOption);
        
    } catch (err) {
        console.error('Failed to load settings:', err);
    }
}

function openFolderPicker() {
    // For now, we'll use a simple prompt to get the custom path
    // In production, you'd use a proper folder picker dialog
    const customPath = prompt('Enter custom download folder path:', appSettings?.download_path || '');
    if (customPath) {
        const pathSelect = document.getElementById('downloadPath');
        const option = document.createElement('option');
        option.value = customPath;
        option.textContent = `📂 ${customPath}`;
        option.selected = true;
        
        // Remove other custom paths
        Array.from(pathSelect.options).forEach(opt => {
            if (opt.value && !opt.value.includes('Downloads') && !opt.value.includes('App Folder') && opt.value !== customPath) {
                opt.remove();
            }
        });
        
        pathSelect.appendChild(option);
    }
}

async function getVideoInfo() {
    const url = document.getElementById('urlInput').value.trim();
    const errorMsg = document.getElementById('errorMsg');
    const loading = document.getElementById('loading');
    const videoSection = document.getElementById('videoSection');
    
    errorMsg.classList.add('hidden');
    
    if (!url) {
        showError('Please enter a video URL');
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
    
    document.getElementById('playlistTitle').textContent = info.title;
    document.getElementById('videoCount').textContent = `${info.videos.length} videos found`;
    
    const videoList = document.getElementById('videoList');
    videoList.innerHTML = '';
    
    info.videos.forEach((video, idx) => {
        const div = document.createElement('div');
        div.className = 'video-card flex items-center gap-4 p-3 glass rounded-xl cursor-pointer';
        div.innerHTML = `
            <span class="text-gray-500 text-sm w-6">${idx + 1}</span>
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
    const downloadPath = document.getElementById('downloadPath').value;
    const playlistMode = document.getElementById('playlistMode').checked;
    
    document.getElementById('inlineProgress').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                url,
                format_id: selectedFormat,
                audio_only: audioOnly,
                download_path: downloadPath,
                playlist_mode: playlistMode
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
            
            // For playlist downloads, show a success message instead of auto-downloading
            if (filename.startsWith('Playlist:')) {
                alert('Playlist download completed! Files saved to your selected folder.');
                resetApp();
            } else {
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
            }
        } else if (progress.status === 'error') {
            eventSource.close();
            document.getElementById('inlineProgress').classList.add('hidden');
            showError(progress.error || 'Download failed');
        } else if (progress.progress !== undefined) {
            let progressText = progress.progress + '%';
            if (progress.current_video && progress.total_videos) {
                progressText = `Video ${progress.current_video}/${progress.total_videos} - ${progress.progress}%`;
            }
            updateProgressBar(progress.progress, progress.speed, progressText);
        }
    };
}

function updateProgressBar(percent, speed, customText) {
    document.getElementById('progressBar').style.width = percent + '%';
    document.getElementById('progressPercent').textContent = customText || percent + '%';
    
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

// Queue Management
let queueRefreshInterval = null;

function toggleQueue() {
    const content = document.getElementById('queueContent');
    const toggle = document.getElementById('queueToggle');
    content.classList.toggle('hidden');
    toggle.classList.toggle('rotate-180');
}

async function loadQueue() {
    try {
        const response = await fetch('/api/queue');
        const data = await response.json();
        
        const queueCount = document.getElementById('queueCount');
        const queueStats = document.getElementById('queueStats');
        const startQueueBtn = document.getElementById('startQueueBtn');
        const clearQueueBtn = document.getElementById('clearQueueBtn');
        const queueEmpty = document.getElementById('queueEmpty');
        const queueList = document.getElementById('queueList');
        
        if (data.total > 0) {
            queueCount.textContent = data.total;
            queueCount.classList.remove('hidden');
            
            const stats = [];
            if (data.pending > 0) stats.push(`${data.pending} pending`);
            if (data.downloading > 0) stats.push(`${data.downloading} downloading`);
            if (data.completed > 0) stats.push(`${data.completed} done`);
            queueStats.textContent = `(${stats.join(', ')})`;
            
            startQueueBtn.classList.remove('hidden');
            clearQueueBtn.classList.remove('hidden');
            
            queueEmpty.classList.add('hidden');
            queueList.classList.remove('hidden');
            
            renderQueueItems(data.queue);
            
            // Expand queue if downloading
            if (data.downloading > 0) {
                document.getElementById('queueContent').classList.remove('hidden');
                document.getElementById('queueToggle').classList.remove('rotate-180');
            }
        } else {
            queueCount.classList.add('hidden');
            queueStats.textContent = '';
            startQueueBtn.classList.add('hidden');
            clearQueueBtn.classList.add('hidden');
            
            queueEmpty.classList.remove('hidden');
            queueList.classList.add('hidden');
        }
        
    } catch (err) {
        console.error('Failed to load queue:', err);
    }
}

function renderQueueItems(queue) {
    const queueList = document.getElementById('queueList');
    queueList.innerHTML = '';
    
    queue.forEach(item => {
        const div = document.createElement('div');
        div.className = `p-3 rounded-xl ${
            item.status === 'downloading' ? 'bg-blue-500/10 border border-blue-500/30' :
            item.status === 'completed' ? 'bg-green-500/10 border border-green-500/30' :
            item.status === 'error' ? 'bg-red-500/10 border border-red-500/30' :
            'bg-gray-800/50 border border-gray-700'
        }`;
        
        let statusIcon, statusText, actionBtn = '';
        
        if (item.status === 'downloading') {
            statusIcon = '<i class="fas fa-spinner fa-spin text-blue-400"></i>';
            statusText = `${item.progress}% ${item.speed ? '• ' + item.speed : ''}`;
        } else if (item.status === 'pending') {
            statusIcon = '<i class="fas fa-clock text-gray-400"></i>';
            statusText = 'Waiting...';
        } else if (item.status === 'completed') {
            statusIcon = '<i class="fas fa-check-circle text-green-400"></i>';
            statusText = item.filename || 'Completed';
            actionBtn = `<button onclick="openFolder('${item.id}')" class="text-xs text-cyan-400 hover:text-cyan-300">
                <i class="fas fa-folder-open mr-1"></i>Open
            </button>`;
        } else if (item.status === 'error') {
            statusIcon = '<i class="fas fa-exclamation-circle text-red-400"></i>';
            statusText = item.error || 'Failed';
            actionBtn = `<button onclick="retryDownload('${item.id}')" class="text-xs text-yellow-400 hover:text-yellow-300">
                <i class="fas fa-redo mr-1"></i>Retry
            </button>`;
        }
        
        div.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="text-lg">${statusIcon}</div>
                <div class="flex-1 min-w-0">
                    <div class="font-semibold truncate text-sm">${item.title || 'Unknown'}</div>
                    <div class="text-xs text-gray-400">${statusText}</div>
                    ${item.status === 'downloading' ? `
                        <div class="mt-2 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                            <div class="h-full bg-gradient-to-r from-cyan-500 to-pink-500 rounded-full transition-all" style="width: ${item.progress}%"></div>
                        </div>
                    ` : ''}
                </div>
                <div class="flex items-center gap-2">
                    ${actionBtn}
                    <button onclick="removeFromQueue('${item.id}')" class="text-gray-500 hover:text-red-400 p-1">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        queueList.appendChild(div);
    });
}

async function addToQueue() {
    const url = document.getElementById('urlInput').value.trim();
    const audioOnly = document.getElementById('audioOnly').checked;
    const downloadPath = document.getElementById('downloadPath').value;
    const title = currentVideoInfo?.title || 'Video';
    
    if (!url) {
        showError('Please enter a video URL');
        return;
    }
    
    try {
        const response = await fetch('/api/queue', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url,
                format_id: selectedFormat,
                audio_only: audioOnly,
                download_path: downloadPath,
                title: title
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        loadQueue();
        
        // Expand queue
        document.getElementById('queueContent').classList.remove('hidden');
        document.getElementById('queueToggle').classList.remove('rotate-180');
        
    } catch (err) {
        showError('Failed to add to queue');
    }
}

function addPlaylistToQueue() {
    if (!currentVideoInfo || currentVideoInfo.type !== 'playlist') {
        showError('No playlist loaded');
        return;
    }
    
    const quality = document.getElementById('playlistQuality').value;
    const startFrom = parseInt(document.getElementById('playlistStart').value) || 1;
    const limit = document.getElementById('playlistLimit').value ? parseInt(document.getElementById('playlistLimit').value) : null;
    const audioOnly = document.getElementById('playlistAudioOnly').checked;
    const downloadPath = document.getElementById('downloadPath').value;
    
    const videos = currentVideoInfo.videos.slice(startFrom - 1, limit ? startFrom - 1 + limit : undefined);
    
    if (videos.length === 0) {
        showError('No videos to add');
        return;
    }
    
    videos.forEach((video, idx) => {
        const videoUrl = `https://www.youtube.com/watch?v=${video.id}`;
        
        fetch('/api/queue', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: videoUrl,
                format_id: quality,
                audio_only: audioOnly,
                download_path: downloadPath,
                title: video.title
            })
        });
    });
    
    // Expand queue and refresh
    setTimeout(() => {
        loadQueue();
        document.getElementById('queueContent').classList.remove('hidden');
        document.getElementById('queueToggle').classList.remove('rotate-180');
    }, 500);
}

function addAllToQueue() {
    addPlaylistToQueue();
}

async function startQueue() {
    try {
        await fetch('/api/queue/start', { method: 'POST' });
        
        // Start polling for updates
        if (queueRefreshInterval) clearInterval(queueRefreshInterval);
        queueRefreshInterval = setInterval(loadQueue, 1000);
        
    } catch (err) {
        showError('Failed to start queue');
    }
}

async function removeFromQueue(taskId) {
    try {
        await fetch(`/api/queue/${taskId}`, { method: 'DELETE' });
        loadQueue();
    } catch (err) {
        console.error('Failed to remove from queue:', err);
    }
}

async function clearCompleted() {
    try {
        await fetch('/api/queue/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'completed' })
        });
        loadQueue();
    } catch (err) {
        console.error('Failed to clear queue:', err);
    }
}

async function retryDownload(taskId) {
    try {
        await fetch(`/api/queue/${taskId}`, { method: 'DELETE' });
        // TODO: Add retry logic
        loadQueue();
    } catch (err) {
        console.error('Failed to retry:', err);
    }
}

function openFolder(taskId) {
    // This would need backend support to get the actual folder path
    alert('Files saved to your selected download folder');
}

// Settings Modal
function showSettings() {
    document.getElementById('settingsModal').classList.remove('hidden');
    document.getElementById('settingsModal').classList.add('flex');
    
    // Load current settings
    document.getElementById('concurrentDownloads').value = appSettings?.concurrent_downloads || 1;
    document.getElementById('concurrentLabel').textContent = appSettings?.concurrent_downloads || 1;
    document.getElementById('defaultQuality').value = appSettings?.default_quality || 'best';
}

function hideSettings() {
    document.getElementById('settingsModal').classList.add('hidden');
    document.getElementById('settingsModal').classList.remove('flex');
}

function updateConcurrentLabel(value) {
    document.getElementById('concurrentLabel').textContent = value;
}

async function saveSettings() {
    const concurrent = document.getElementById('concurrentDownloads').value;
    const quality = document.getElementById('defaultQuality').value;
    
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                concurrent_downloads: concurrent,
                default_quality: quality
            })
        });
        
        const data = await response.json();
        appSettings = data.settings;
        
        hideSettings();
    } catch (err) {
        showError('Failed to save settings');
    }
}

// Load settings on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadQueue();
});

// Discovery Functions
let discoveredVideos = [];
let discoverEventSource = null;

async function discoverVideos() {
    const url = document.getElementById('urlInput').value.trim();
    const maxVideos = parseInt(document.getElementById('discoverLimit').value) || 50;
    const errorMsg = document.getElementById('errorMsg');
    
    errorMsg.classList.add('hidden');
    
    if (!url) {
        showError('Please enter a video URL');
        return;
    }
    
    // Show discovery panel
    document.getElementById('discoveryPanel').classList.remove('hidden');
    document.getElementById('discoverProgress').classList.remove('hidden');
    document.getElementById('discoveredList').innerHTML = '';
    document.getElementById('discoverCount').textContent = '0';
    document.getElementById('discoverStatus').textContent = 'Starting...';
    discoveredVideos = [];
    
    try {
        const response = await fetch('/api/discover', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                max_videos: maxVideos
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // Start listening to discovery stream
        discoverEventSource = new EventSource(`/api/discover/${data.task_id}`);
        
        discoverEventSource.onmessage = function(event) {
            const result = JSON.parse(event.data);
            
            if (result.type === 'video') {
                // New video discovered
                discoveredVideos.push(result.video);
                addDiscoveredVideo(result.video, discoveredVideos.length);
                document.getElementById('discoverCount').textContent = discoveredVideos.length;
                document.getElementById('discoverStatus').textContent = `Found ${discoveredVideos.length} videos`;
            }
            
            if (result.status === 'completed') {
                document.getElementById('discoverProgress').classList.add('hidden');
                document.getElementById('discoverStatus').textContent = `Discovery complete! Found ${result.count} videos`;
                discoverEventSource.close();
            }
            
            if (result.status === 'error') {
                document.getElementById('discoverProgress').classList.add('hidden');
                showError(result.error || 'Discovery failed');
                discoverEventSource.close();
            }
        };
        
    } catch (err) {
        showError('Failed to start discovery');
    }
}

function addDiscoveredVideo(video, index) {
    const list = document.getElementById('discoveredList');
    const div = document.createElement('div');
    div.className = 'video-card flex items-center gap-3 p-3 glass rounded-xl cursor-pointer';
    div.dataset.index = index - 1;
    div.dataset.url = video.url;
    div.dataset.title = video.title;
    div.onclick = (e) => {
        if (e.target.type !== 'checkbox') {
            const checkbox = div.querySelector('input[type="checkbox"]');
            checkbox.checked = !checkbox.checked;
        }
    };
    
    div.innerHTML = `
        <input type="checkbox" class="w-5 h-5 accent-cyan-400" checked>
        <span class="text-gray-500 text-sm w-6">${index}</span>
        <img src="${video.thumbnail}" class="w-24 h-14 object-cover rounded" alt="${video.title}">
        <div class="flex-1 min-w-0">
            <div class="font-semibold truncate text-sm">${video.title}</div>
            <div class="text-xs text-gray-400">${video.duration}</div>
        </div>
    `;
    
    list.appendChild(div);
}

function selectAllDiscovered() {
    document.querySelectorAll('#discoveredList input[type="checkbox"]').forEach(cb => cb.checked = true);
}

function deselectAllDiscovered() {
    document.querySelectorAll('#discoveredList input[type="checkbox"]').forEach(cb => cb.checked = false);
}

async function addSelectedToQueue() {
    const selectedVideos = [];
    document.querySelectorAll('#discoveredList .video-card').forEach(div => {
        const checkbox = div.querySelector('input[type="checkbox"]');
        if (checkbox.checked) {
            selectedVideos.push({
                url: div.dataset.url,
                title: div.dataset.title
            });
        }
    });
    
    if (selectedVideos.length === 0) {
        showError('No videos selected');
        return;
    }
    
    const quality = document.getElementById('discoverQuality').value;
    const audioOnly = document.getElementById('discoverAudioOnly').checked;
    const downloadPath = document.getElementById('downloadPath').value;
    
    let addedCount = 0;
    for (const video of selectedVideos) {
        try {
            await fetch('/api/queue', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: video.url,
                    format_id: quality,
                    audio_only: audioOnly,
                    download_path: downloadPath,
                    title: video.title
                })
            });
            addedCount++;
        } catch (err) {
            console.error('Failed to add video to queue:', err);
        }
    }
    
    // Refresh queue and show it
    loadQueue();
    document.getElementById('queueContent').classList.remove('hidden');
    document.getElementById('queueToggle').classList.remove('rotate-180');
    
    alert(`Added ${addedCount} videos to queue!`);
}
