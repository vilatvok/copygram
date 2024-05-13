document.addEventListener('DOMContentLoaded', (event) => {
    const protocol = window.location.protocol == 'https:' ? 'wss': 'ws'
    const chatSocket = new WebSocket(
        protocol +
        '://' +
        window.location.host +
        '/ws/chat_api/' +
        url_name +
        '/' + 
        chat_id +
        '/'
    );

    chatSocket.onopen = function(){
        chatSocket.send(
            JSON.stringify({
                pk:chat_id,
                action:"retrieve",
                request_id:request_id,
            })
        );
        chatSocket.send(
            JSON.stringify({
                pk:chat_id,
                action:"subscribe_to_messages_in_room",
                request_id:request_id,
            })
        );
        chatSocket.send(
            JSON.stringify({
                pk:chat_id,
                action:"subscribe_instance",
                request_id:request_id,
            })
        );
    };

    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        console.log(data);
    };

    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };

    function clear_chat(event) {
        document.getElementById('clear-chat').addEventListener('click', function(event) {
            event.preventDefault();
            chatSocket.send(JSON.stringify({
                url: url_name,
                pk:chat_id,
                action:"clear_messages",
                request_id:request_id,
            }));
        })
    }

    if (url_name == 'room') {
        document.getElementById('leave-chat').addEventListener('click', function(event) {
            event.preventDefault();
            chatSocket.send(JSON.stringify({
                pk:chat_id,
                action:"leave_room",
                request_id:request_id,
            }));
            window.location.href = url;
        })
        // const members = document.querySelectorAll('.remove-user');

        // members.forEach(button => {
        //     button.addEventListener('click', function (event) {
        //         event.preventDefault();
        //         const user = button.getAttribute('id');
        //         const split = user.split('-');
        //         const user_id = split[1];
        //         chatSocket.send(JSON.stringify({
        //             pk: chat_id,
        //             user_id: user_id,
        //             action: "remove_user",
        //             request_id: request_id
        //         }));
        //         count_members -= 1;
        //         if (count_members < 2) {
        //             window.location.href = url;
        //         }
        //     });
        // })

        // const add_users = document.querySelectorAll('.add-user')

        // add_users.forEach(button => {
        //     button.addEventListener('click', function (event) {
        //         event.preventDefault();
        //         const user = button.getAttribute('id');
        //         const split = user.split('-');
        //         const user_id = split[1];
        //         chatSocket.send(JSON.stringify({
        //             pk: chat_id,
        //             user_id: user_id,
        //             action: "add_user",
        //             request_id: request_id
        //         }));
        //         count_members += 1;
        //         if (count_members < 2) {
        //             window.location.href = url;
        //         }
        //     });
        // })
        if (user == owner) {
            clear_chat();
        }
    } else {
        clear_chat();
    }

    function send_message(event) {
        document.querySelector('#message-sent').onclick = function(e){
            const messageInput = document.querySelector('#message-input');
            const message = messageInput.value;
            if (message.trim() === "") {
                alert("Please enter a message before sending.");
                return;
            }
            chatSocket.send(JSON.stringify({
                url: url_name,
                message: message,
                pk: chat_id,
                action: "create_message",
                request_id: request_id
            }));
            messageInput.value = '';
        };
    };
    send_message();
})