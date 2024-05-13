document.addEventListener('DOMContentLoaded', (event) => {
    const csrftoken = Cookies.get("csrftoken")
    const like_button = document.getElementById("likes");
    const like_action = document.getElementById("is_like")
    const likes_count = document.getElementById("total_likes");
    like_button.addEventListener("click", function(event) {
        event.preventDefault();
        const options = {
            method: 'POST',
            headers: {'X-CSRFToken': csrftoken},
            mode: 'same-origin'
        }
        fetch(like_url, options)
            .then(response => response.json())
            .then(data => {
                var total = parseInt(likes_count.innerHTML)
                likes_count.innerHTML = data.status === 'Liked' ? total + 1 : total - 1;
                like_action.innerHTML = data.status === 'Liked' ? `likes &#10084;` : `likes &#9825;`
            })
            .catch(error => {
                console.error("Fetch error", error)
            })
        })

    const deleteButtons = document.querySelectorAll('.delete-comment');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault()
            const comment = button.getAttribute('id')
            const split = comment.split('-')
            const comment_id = split[1]
            const options = {
                method: 'DELETE',
                headers: {'X-CSRFToken': csrftoken},
                mode: 'same-origin'
            }
            // Make a request to delete the comment
            fetch(comment_url.replace('0', comment_id), options)
                .then(response => response.json())
                .then(data => {
                    if (data["status"] == "Ok") {
                        const commentElement = document.querySelector('.card.mb-4');
                        commentElement.remove()
                    }
                })
                .catch(error => {
                    console.error("Fetch error", error);
                });
        });
    })

    const playVideo = document.querySelectorAll('.playVideo')
    playVideo.forEach(btn => {
        btn.addEventListener('click', function(event) {
            if (btn.paused){
                btn.play();
            } else {
                btn.pause();
            }
        })
    })
})