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
   
   statusSocket.onmessage = function(event) {
      const data = JSON.parse(event.data)
      const users_ = document.querySelectorAll('.rounded-pill')
      users_.forEach(mark => {
         const mark_one = mark.getAttribute('id')
         const split_one = mark_one.split('-')
         const __user = split_one[1]
         if (data.users.includes(__user)) {
            const elem = document.querySelector(`[id="status-${__user}"]`)
            elem.innerHTML = 'Online'
         }
      })
   };
})