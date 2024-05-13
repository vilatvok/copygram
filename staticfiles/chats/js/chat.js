document.addEventListener('DOMContentLoaded', (event) => {
    const chat = document.getElementById('msg')

    let temp_count = 0;
    const protocol = window.location.protocol == 'https:' ? 'wss': 'ws'
    const chatSocket = new WebSocket(
        protocol +
        '://' +
        window.location.host +
        '/ws/chat/' +
        chat_id +
        '/'
    );
    chat.scrollTop = chat.scrollHeight;

    chatSocket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        switch (data.action) {
            case "clear_messages":
                chat.innerHTML = `<p class="fw-bold">Send your first message</p>`;
                temp_count = 0;
                break;
            case "leave_room":
                chat.innerHTML += `<p class="fw-bold">${data.user} leave this room</p>`;
                if (data.user == user) {
                    window.location.href = url;
                }
                break;
            case "send_message":
                const curr_user = data.user === user;
                const currentDate = new Date();
                // Format the date according to the desired format
                const formattedDate = `${currentDate.toLocaleString('en-us',
                    { month: 'short' })}. ${currentDate.getDate()}, ${currentDate.getFullYear()}, 
                    ${currentDate.getHours()}:${currentDate.getMinutes()} 
                    ${currentDate.getHours() >= 12 ? 'p.m.' : 'a.m.'}`;
                if (curr_user) {
                    chat.innerHTML += `
                        <div class="d-flex justify-content-end">
                            <p class="small mb-1 text-muted">${formattedDate}</p>
                        </div>
                        <div class="d-flex flex-row justify-content-end mb-4 pt-1">
                            <div>
                                <p class="small p-2 me-3 mb-3 text-white rounded-3 bg-success" 
                                style="word-wrap: break-word; max-width: 250px;">
                                <span class="fw-bold">Me</span>
                                <br>
                                ${  
                                    data.files
                                    ? data.files.map(file => `
                                        <a href="/media/messages/${file[1]}"><img src="/media/messages/${file[1]}" style="width:200px; height:100%"></a>
                                    `).join('') : ''
                                }
                                ${data.message}</p>
                            </div>
                            <img src=${data.avatar}
                                alt="avatar 1" style="width: 45px; height:100%; border-radius: 20px;">
                        </div>
                    `;
                } else {
                    chat.innerHTML += `
                        <div class="d-flex justify-content-start">
                            <p class="small mb-1 text-muted">${formattedDate}</p>
                        </div>
                        <div class="d-flex flex-row justify-content-start mb-4 pt-1">
                            <img src=${data.avatar}
                                alt="avatar 1" style="width: 45px; height:100%; border-radius: 20px;">
                            <div>
                                <p class="small p-2 ms-3 mb-3 text-white rounded-3 bg-success" 
                                    style="word-wrap: break-word; max-width: 250px;">
                                    <span class="fw-bold">${data.user}</span>
                                    <br>
                                    ${
                                        data.files
                                        ? data.files.map(file => `
                                            <a href="/media/messages/${file[1]}"><img src="/media/messages/${file[1]}" style="width:200px; height:100%"></a>
                                        `).join('') : ''
                                    }
                                    ${data.message}
                                </p>
                            </div>
                        </div>
                    `;
                }
                chat.scrollTop = chat.scrollHeight;
                temp_count += 1;
                break;
        }
    };

    chatSocket.onclose = function(event) {
        console.error('Chat socket closed unexpectedly');
    };
    function toDataURL(file, callback) {
        var reader = new FileReader();
        reader.onload = function () {
            var dataURL = reader.result;
            callback(dataURL);
        }
        reader.readAsDataURL(file);
    }

    document.querySelector('#message-sent').onclick = function (event) {
        const messageInput = document.querySelector('#message-input');
        const message = messageInput.value;

        const files = document.getElementById('customFile');
        if (message.trim() === "" && files.files.length === 0) {
            return;
        } else if (files.files.length === 0) {
            chatSocket.send(JSON.stringify({
                'action': 'send_message',
                'url': url_name,
                'chat': chat_id,
                'user': user,
                'avatar': avatar,
                'message': message,
            }))
            messageInput.value = '';
        } else {
            const promises = [];
            const files_list = [];
            for (const file of files.files) {
                const promise = new Promise((resolve) => {
                    toDataURL(file, function (dataURL) {
                        files_list.push([dataURL, file.name]);
                        resolve(); // Resolve the promise once the message is sent
                    });
                });
                promises.push(promise);
            }

            // Wait for all promises to resolve before clearing input values
            Promise.all(promises).then(() => {
                chatSocket.send(JSON.stringify({
                    'action': 'send_message',
                    'url': url_name,
                    'chat': chat_id,
                    'user': user,
                    'avatar': avatar,
                    'message': message,
                    'files': files_list,
                }));
                console.log(files_list);
                messageInput.value = '';
                files.value = '';
            });
        }
    };

    function clear_chat(event) {
        document.getElementById('clear-chat').addEventListener('click', function(event) {
            const messages = {
                'action': 'clear_messages',
                'chat': chat_id,
                'url': url_name,
            };
            chatSocket.send(JSON.stringify(messages));
        })
    }

    if (url_name == 'room') {
        if (user == owner) {
            clear_chat();
        } 
        document.getElementById('leave-chat').addEventListener('click', function(event) {
            const room = {
                'action': 'leave_room',
                'chat': chat_id,
                'user': user,
            };
            chatSocket.send(JSON.stringify(room));
        })
    } else {
        clear_chat();
        if (count_messages == 0) {
            window.onbeforeunload = function(event) {
                if (temp_count == 0) {
                    chatSocket.send(JSON.stringify({
                        'action': 'remove_chat',
                        'chat': chat_id
                    }));
                }
                return 'Bye';
            }
            
        }
    }
})