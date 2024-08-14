
function disableScroll() {
    document.body.style.overflow = 'hidden';
}

function enableScroll() {
    document.body.style.overflow = 'auto';
}

function createWinFolder () {
    const rootWin = document.getElementById('root-win');
    rootWin.innerHTML = `<div class="window-background">
            <div class="window">
                <div class="window-content">
                    <div class="window-top">
                        <div class="window-top-label">Новая папка</div>
                        <a href="javascript: destroyWin()" class="window-top-close">
                            <img class="window-top-close-img" src="/static/img/cross.svg" alt="">
                        </a>
                    </div>
                    <div class="window-middle">
                        <div class="window-middle-row">
                          <label class="window-middle-label">Название</label>
                          <input class="modal-base-input middle-input" type="text" autocomplete="off" id="form-folder">
                        </div>
                    </div>
                    <div class="window-bottom">
                        <a class="modal-base-button" href="javascript: addFolder()">Создать</a>
                    </div>
                </div>
                
            </div>
        </div>`
    disableScroll();
}


function createWinAddState () {
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
                          <input class="modal-base-input middle-input" type="text" autocomplete="off" id="form-theme">
                        </div>
                        <div class="window-middle-row">
                          <label class="window-middle-label">Для кого</label>
                          <input class="modal-base-input middle-input" type="text" autocomplete="off" placeholder="можно не заполнять" id="form-whom">
                        </div>
                        <div class="window-middle-row">
                          <label class="window-middle-label">Информация</label>
                          <textarea class="modal-base-input middle-textarea" autocomplete="off" id="form-info"></textarea>
                        </div>
                    </div>
                    <div class="window-bottom">
                        <a class="modal-base-button" href="javascript: addState()">Создать</a>
                    </div>
                </div>
                
            </div>
        </div>`
    disableScroll();
}


function createWinChangeState (id) {
    $.ajax({
        type: "get",
        url: "/connect_statements/" + id,
        dataType: "json",
        success: function (response, _ ,xhr) {
            if (xhr.status == 200) {
                const rootWin = document.getElementById('root-win');
                rootWin.innerHTML = `<div class="window-background">
                    <div class="window">
                        <div class="window-content">
                            <div class="window-top">
                                <div class="window-top-label">${response.name}</div>
                                <a href="javascript: destroyWin()" class="window-top-close">
                                    <img class="window-top-close-img" src="/static/img/cross.svg" alt="">
                                </a>
                            </div>
                            <div class="window-middle">
                                
                            </div>
                            <div class="window-bottom">
                                <input class="modal-base-input send-input" type="text">
                                <a class="modal-base-button" href="javascript: sendMessage(${id})">Отправить</a>
                            </div>
                        </div>

                    </div>
                </div>`
                updateMessages(id);
                disableScroll();
                $('.send-input').on('keydown', function (e) { 
                    //e.preventDefault();
                    if (e.key == 'Enter') {
                        sendMessage(id);
                    }
                    
                });
            } else {
                alert('Не удалось закрыть заявку');
            }
        },
    });
    
}


function createWinChangeWhom (id) {
    $.ajax({
        type: "get",
        url: "/connect_statements/" + id,
        dataType: "json",
        success: function (response, _ ,xhr) {
            if (xhr.status == 200) {
                const rootWin = document.getElementById('root-win');
                rootWin.innerHTML = `<div class="window-background">
                    <div class="window">
                        <div class="window-content">
                            <div class="window-top">
                                <div class="window-top-label">Изменение дополнительной надписи</div>
                                <a href="javascript: destroyWin()" class="window-top-close">
                                    <img class="window-top-close-img" src="/static/img/cross.svg" alt="">
                                </a>
                            </div>
                            <div class="window-middle">
                                <input type="text" class="modal-base-input middle-input" value="${response.for_whom}" id="for_whom_input">
                                <fieldset>
                                    <legend>Выбор цвета</legend>
                                        <div style="display:flex; margin-top:5px;">
                                            <input type="radio" value="red" name="color-pick" checked>
                                            <div style="background-color:red; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="DarkRed" name="color-pick">
                                            <div style="background-color:DarkRed; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="Goldenrod" name="color-pick">
                                            <div style="background-color:Goldenrod; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="SaddleBrown" name="color-pick">
                                            <div style="background-color:SaddleBrown; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="DodgerBlue" name="color-pick">
                                            <div style="background-color:DodgerBlue; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="Blue" name="color-pick">
                                            <div style="background-color:Blue; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="LimeGreen" name="color-pick">
                                            <div style="background-color:LimeGreen; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="Green" name="color-pick">
                                            <div style="background-color:Green; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="DarkSlateGray" name="color-pick">
                                            <div style="background-color:DarkSlateGray; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="DarkViolet" name="color-pick">
                                            <div style="background-color:DarkViolet; width:20px; height:20px; display:block";></div>
                                        </div>
                                        <div style="display:flex; margin-top:5px;"">
                                            <input type="radio" value="Black" name="color-pick">
                                            <div style="background-color:Black; width:20px; height:20px; display:block";></div>
                                        </div>
                                </fieldset>
                            </div>
                            <div class="window-bottom">
                                <a class="modal-base-button" href="javascript: sendForWhom(${id})">Сохранить</a>
                            </div>
                        </div>

                    </div>
                </div>`
                disableScroll();
            } else {
                alert('Не удалось закрыть заявку');
            }
        },
    });
    
}

function createWinChangeFolder (id) { 
    $.ajax({
        type: "get",
        url: "/connect_statements/folders",
        dataType: "json",
        success: function (response_folders, _ ,xhr) {
            if (xhr.status == 200) {
                const rootWin = document.getElementById('root-win');
                rootWin.innerHTML = `<div class="window-background">
                    <div class="window">
                        <div class="window-content">
                            <div class="window-top">
                                <div class="window-top-label">Переместить в папку</div>
                                <a href="javascript: destroyWin()" class="window-top-close">
                                    <img class="window-top-close-img" src="/static/img/cross.svg" alt="">
                                </a>
                            </div>
                            <div class="window-middle">
                                <label>Текущая папка: не выбрана</label>
                                <select style="margin-top: 20px;">
                                    <option value="">--Выберите папку--</option>
                                    
                                </select>
                            </div>
                            <div class="window-bottom">
                                <a class="modal-base-button" href="javascript: replaceStatementToFolder(${id})">Сохранить</a>
                            </div>
                        </div>

                    </div>
                </div>`
                disableScroll();
                $.ajax({
                    timeout: 2000,
                    type: "get",
                    url: "/connect_statements/" + id,
                    dataType: "json",
                    success: function (response) {
                        $.each(response_folders, function (indexInArray, valueOfElement) { 
                            let htmlDoc = `
                            <option value="${valueOfElement.id}">${valueOfElement.name}</option>
                            `
                            $(htmlDoc).appendTo(".window-middle select");
                            if (valueOfElement.id == response.folder_id) {
                                $('.window-middle label').text('Текущая папка:' + valueOfElement.name);
                            }
                        });
                    }
                });
            } else {
                alert('Не удалось изменить папку');
            }
        },
    });
}


function saveForWhom(id) {
    $.ajax({
        type: "method",
        url: "url",
        data: "data",
        dataType: "dataType",
        success: function (response) {
            
        }
    });
}

function destroyWin(update=false) {
    const rootWin = document.getElementById('root-win');
    rootWin.innerHTML = '';
    enableScroll();
    if (update) {
        loadOpenStatements();
    }
}