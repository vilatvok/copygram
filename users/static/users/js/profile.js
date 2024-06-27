document.addEventListener('DOMContentLoaded', (event) => {
   const csrftoken = Cookies.get("csrftoken")
   const follow_btn = document.getElementById("follow")
   const followers_count = document.getElementById("followers")
   follow_btn.addEventListener('click', function(event) {
      event.preventDefault();
      const options = {
         method: 'POST',
         headers: {'X-CSRFToken': csrftoken},
         mode: 'same-origin'
      }
      fetch(url, options)
         .then(response => response.json())
         .then(data => {
            var total = parseInt(followers_count.innerHTML)
            switch (data.status) {
               case 'Followed':
                  follow_btn.innerHTML = 'Unfollow'
                  followers_count.innerHTML = total + 1 + ' '
                  break;
               case 'Unfollowed':
                  follow_btn.innerHTML = 'Follow'
                  followers_count.innerHTML = total - 1 + ' '
                  break;
               case 'Request was sent':
                  follow_btn.innerHTML = 'Cancel'
                  break;
               case 'Canceled':
                  follow_btn.innerHTML = 'Follow'
                  break;
            }
         })
         .catch(error => {
            console.error(error);
         })
   })
})