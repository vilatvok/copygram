const protocol = window.location.protocol == 'https:' ? 'wss': 'ws'
const statusSocket = new WebSocket(
    protocol + '://' + window.location.host + '/ws/status/'
);

statusSocket.onopen = function(event) {
    console.log('Socket connected');
    statusSocket.send(JSON.stringify({
        'user': user_,
        'status': 'Online'
    }))
};

statusSocket.onmessage = function(event) {
    const data = JSON.parse(event.data)
    if (data.users.includes(user_)) {
        set_status(data.status);
    }
};

statusSocket.onclose = function(event) {
    console.error('Socket closed unexpectedly');
};

window.onbeforeunload = function(event) {
    statusSocket.send(JSON.stringify({
        'user': user_,
        'status': 'Offline'
    }))
}

function set_status(status) {
    const statusElement = document.querySelector('.rounded-pill');
    statusElement.textContent = status;
}