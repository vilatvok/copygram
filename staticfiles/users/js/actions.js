document.addEventListener('DOMContentLoaded', (event) => {
   const csrftoken = Cookies.get("csrftoken")
   const btn = document.querySelectorAll(".delete-action")
   btn.forEach(button => {
      button.addEventListener('click', function(event) {
         event.preventDefault();
         const action = button.getAttribute("id")
         const split = action.split("-")
         const action_id = split[1]
         const options = {
            method: 'DELETE',
            headers: {'X-CSRFToken': csrftoken},
            mode: 'same-origin'
         }
         fetch(url.replace('0', action_id), options)
            .then(response => response.json())
            .then(data => {
               if (data["status"] == "Ok") {
                  const action_element = document.querySelector(".card.w-75")
                  action_element.remove()
               }         
            })
            .catch(error => {
               console.error(error)
            })
      })
   })
})