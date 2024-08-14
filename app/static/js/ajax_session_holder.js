
/*
Для удобства этот JS подключается к Header-Menu, так это меню присутсвует на всех страница (почти)
Так проще трекать онлайн сейчас User или нет
*/

function sessionHold() {
    $.ajax({
        type: "post",
        url: "/connected",
        dataType: "text",
        timeout: 3000,
        success: function (response) {
            if (response == 'logout') {
                window.location = '/logout';
            }
        }
    });
}

sessionHold();

setInterval(() => {
    sessionHold();
}, 5000);