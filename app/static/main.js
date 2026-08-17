window.addEventListener('DOMContentLoaded', loadHistory);

async function loadHistory() {
    const list = document.getElementById('historyList');
    try {
        const res = await fetch('/meetings');
        const meetings = await res.json();
        list.innerHTML = '';
        
        if (meetings.length === 0) {
            list.innerHTML = '<p style="color: #9ca3af; text-align: center; font-size: 14px;">No meetings loaded yet</p>';
            return;
        }

        meetings.forEach(m => {
            const item = document.createElement('div');
            item.className = 'history-item';
            item.onclick = () => showMeetingDetails(m);
            const badgeClass = m.status === 'completed' ? 'badge-completed' : 'badge-processing';
            item.innerHTML = `
                <span style="font-weight: 500; font-size: 14px; max-width: 70%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    Meeting #${m.id}: ${m.filename}
                </span>
                <span class="badge ${badgeClass}">${m.status}</span>
            `;
            list.appendChild(item);
        });
    } catch (err) {
        list.innerHTML = '<p style="color: #fca5a5; font-size: 14px;">Error loading history</p>';
    }
}

function showMeetingDetails(meeting) {
    if (meeting.status !== 'completed') {
        alert('This meeting is still being processed by AI. Please wait.');
        return;
    }
    document.getElementById('statusBlock').classList.add('hidden');
    document.getElementById('resultBlock').classList.remove('hidden');
    document.getElementById('summaryText').innerText = meeting.summary;
    document.getElementById('transcriptText').innerText = meeting.transcript;
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('audioFile');
    const statusBlock = document.getElementById('statusBlock');
    const resultBlock = document.getElementById('resultBlock');
    
    if (!fileInput.files.length) return;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    statusBlock.classList.remove('hidden');
    statusBlock.className = "status status-loading";
    statusBlock.innerText = "⏳ Uploading audio file to server...";
    resultBlock.classList.add('hidden');

    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const data = await response.json();
        
        if (response.status !== 201) {
            throw new Error(data.detail || "Upload failed");
        }

        loadHistory();
        checkStatus(data.id);
    } catch (err) {
        statusBlock.className = "status status-error";
        statusBlock.innerText = `❌ Error: ${err.message}`;
    }
});

async function checkStatus(id) {
    const statusBlock = document.getElementById('statusBlock');
    statusBlock.className = "status status-processing";
    statusBlock.innerText = "🤖 AI is transcribing and summarizing your meeting. Please wait...";

    const interval = setInterval(async () => {
        const res = await fetch(`/meetings/${id}`);
        const data = await res.json();

        if (data.status === 'completed') {
            clearInterval(interval);
            statusBlock.classList.add('hidden');
            loadHistory();
            document.getElementById('resultBlock').classList.remove('hidden');
            document.getElementById('summaryText').innerText = data.summary;
            document.getElementById('transcriptText').innerText = data.transcript;
        }
    }, 2000);
}
