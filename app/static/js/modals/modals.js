
function disableScroll() {
    document.body.style.overflow = 'hidden';
}

function enableScroll() {
    document.body.style.overflow = 'auto';
}


function createWinAddState (theme, id) {
    const rootWin = document.getElementById('root-win');
    rootWin.innerHTML = `<div class="window-background">
            <div class="window">
                <div class="window-content">
                    <div class="window-top">
                        <div class="window-top-label">Новая заявка</div>
                        <a href="javascript: destroyWin()" class="window-top-close">
                            <img class="window-top-close-img" src="/static/img/cross.svg" alt="">
                        </a>
                    </div>
                    <div class="window-middle">
                        
                        <div class="window-middle-row">
                          <label class="window-middle-label">Тема</label>
                          <input class="modal-base-input middle-input" type="text" autocomplete="off" id="form-theme" value="${theme}">
                        </div>
                        
                        <div class="window-middle-row">
                          <label class="window-middle-label">Информация</label>
                          <textarea class="modal-base-input middle-textarea" autocomplete="off" id="form-info"></textarea>
                        </div>
                    </div>
                    <div class="window-bottom">
                        <a id="create_statement" class="modal-base-button" href="javascript:createStatement('${id}')">Создать</a>
                    </div>
                </div>
                
            </div>
        </div>`
    disableScroll();
}

function createStatement(id) {
    $('#create_statement').removeAttr('href');
    $('#create_statement').text('Отправка..');
    $('#create_statement').css('cursor', 'pointer')

    $.ajax({
        timeout: 5000,
        type: "get",
        url: "/helpdesk/create/",
        data: {
            iid: id,
            subj: $('#form-theme').val(),
            info: $('#form-info').val(),
        },
        dataType: "json",
        success: function (response) {
            destroyWin();
            if ('success' in response) {
                window.location.href = '/helpdesk/';
            } else {
                alert('Не удалось создать новую заявку')
            }
            
        },
        error: function () {
            destroyWin();
            alert('Не удалось создать новую заявку')
        }
    });
}

function destroyWin(update) {
    const rootWin = document.getElementById('root-win');
    rootWin.innerHTML = '';
    enableScroll();
    
}

