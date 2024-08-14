

//Обработчик события отправки формы
function handleForm(event) {
    event.preventDefault();

    let request = new XMLHttpRequest();
    request.open('POST', url)
}




function openWindowAddHost(url) {
    //Открыть modal-window добавления хоста
    //Привязывается к кнопке

    let request = new XMLHttpRequest();
    request.open('GET', url)
    request.addEventListener('readystatechange', () => {
        if (request.readyState === 4 && request.status === 200) {

            //вставка html формы с backend'a
            document.querySelector('.div-place-modal').innerHTML = request.responseText;

            //ловим событие отрпавки формы и останавливаем отправку
            //нужно для того чтобы валидация полей выполнялась, а отправка нет
            document.querySelector('.modal-form').addEventListener('submit', handleForm)
        }
    })

    request.send();
    
}


function closeWindow() {
    //Закрыть modal-window для всех
    //Привязывается к кнопке отменить

    document.querySelector('.div-place-modal').innerHTML = '';
}

function compareContent() {
    let hosts_list = $('.host-table tbody').children();
    
    for (let i = 0; i < hosts_list.length; i++) {
        let state = hosts_list[i].children[0].textContent;
        let name = hosts_list[i].children[1].textContent;
        let ip = hosts_list[i].children[2].textContent;
        let change_state = hosts_list[i].children[3].textContent;
        console.log(state, name, ip, change_state);
    }
    

}

function updateContentLoop(response) {

    //for (let i=0; i < response.length; i++ ) {
    //    console.log(response[i]);
    //}
    compareContent()

    setTimeout(loadContent, 1000);
}


function loadContent() {
    $.ajax({
        type: "GET",
        url: window.location.href,
        data: "data=json",
        dataType: "json",
        success: updateContentLoop
    });
}


// $(document).ready(function () {
//     loadContent()
// });



