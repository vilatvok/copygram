document.addEventListener('DOMContentLoaded', (event) => {    
    const csrftoken = Cookies.get("csrftoken");
    const users = document.querySelectorAll(".follow-recomendation");
    users.forEach(button => {
    button.addEventListener('click', function(event) {
        event.preventDefault();
        const user = button.getAttribute('id');
        const split = user.split('-');
        const user_slug = split[1];
        const options = {
            method: 'POST',
            headers: {'X-CSRFToken': csrftoken},
            mode: 'same-origin'
        }
        fetch(url.replace(users_slug, user_slug), options)
            .then(response => response.json())
            .then(data => {
                button.innerHTML = data.status === 'Follow' ? 'Unfollow': 'Follow'
            })
            .catch(error => {
                console.error(error);
            })
        });
    });
})