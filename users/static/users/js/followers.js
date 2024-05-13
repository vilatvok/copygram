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
               switch (data.status) {
                  case 'Followed':
                     button.innerHTML = 'Unfollow'
                     followersElement.innerHTML = total + 1 +  ''
                     break;
                  case 'Unfollowed':
                     button.innerHTML = 'Follow'
                     followersElement.innerHTML = total - 1 + ' '
                     break;
                  case 'Request was sent':
                     button.innerHTML = 'Cancel'
                     break;
                  case 'Canceled':
                     button.innerHTML = 'Follow'
                     break;
               }
            })
            .catch(error => {
               console.error(error);
            })
      })
   })
})