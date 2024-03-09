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
            follow_btn.innerHTML = data.status === 'Follow' ? 'Unfollow': 'Follow'
            followers_count.innerHTML = data.status === 'Follow' ? total + 1 + ' ' : total - 1 + ' '
         })
         .catch(error => {
            console.error(error);
         })
   })
})