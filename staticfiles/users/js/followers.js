document.addEventListener('DOMContentLoaded', (event) => {
   const csrftoken = Cookies.get("csrftoken")
   const users = document.querySelectorAll(".me-1")
   users.forEach(button => {
      button.addEventListener('click', function(event) {
         event.preventDefault();
         const user_ = button.getAttribute('id')
         const split = user_.split('-')
         const user_slug = split[1]
         const followersElement = document.querySelector(`[id="${user_slug}"]`);
         const options = {
            method: 'POST',
            headers: {'X-CSRFToken': csrftoken},
            mode: 'same-origin'
         }
         fetch(url.replace('0', user_slug), options)
            .then(response => response.json())
            .then(data => {
               var total = parseInt(followersElement.innerHTML)
               button.innerHTML = data.status === 'Follow' ? 'Unfollow': 'Follow'
               followersElement.innerHTML = data.status === 'Follow' ? total + 1 + ' ' : total - 1 + ' '
            })
            .catch(error => {
               console.error(error);
            })
      })
   })
})