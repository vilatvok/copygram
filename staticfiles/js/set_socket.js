const protocol = window.location.protocol == 'https:' ? 'wss': 'ws'
const statusSocket = new WebSocket(
    protocol + '://' + window.location.host + '/ws/status/'
);

statusSocket.onopen = function(event) {
    console.log('Socket connected');
    statusSocket.send(JSON.stringify({
        'user': user,
        'status': 'Online',
    }))
};

statusSocket.onclose = function(event) {
    console.error('Socket closed unexpectedly');
};

window.onbeforeunload = function(event) {
    statusSocket.send(JSON.stringify({
        'user': user,
        'status': 'Offline'
    }))
}