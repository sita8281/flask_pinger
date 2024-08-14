// имитация для меня Питоновского asyncio.sleep()
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

let loading_anim = null;
let err_anim = null;
let helpdesk_add = null;


// функция подгрузки пока невидимого контента,
// если хоть один блок не загрузится callback 
// не будет вызван
async function loadAllModules(callback) {
    let response = await fetch('/helpdesk/loading/');
    let response2 = await fetch('/helpdesk/loading_err/');
    let _helpdesk_add = await fetch('/helpdesk/helpdesk_add/')
    if (response.ok && response2.ok && _helpdesk_add.ok) {
        loading_anim = await response.text()
        err_anim = await response2.text()
        helpdesk_add = await _helpdesk_add.text()
        await callback();
    }
}

// упрощенная функция для втсавки блоков в блок списка заявок
function innerBlock(html, block, displ=true) {
    let bl = document.getElementsByClassName(block)[0]
    bl.innerHTML = html;
    if (displ) {
        bl.style.display = 'flex';
    }
}

function closeBlock(block) {
    document.getElementsByClassName(block)[0].style.display = 'none';
}

async function showHelpDesk() {
    innerBlock(loading_anim, 'statement-list');
    let response = await fetch('/helpdesk/helpdesk_list/')
    if (response.ok) {
        innerBlock(await response.text(), 'statement-list');
    } else {
        innerBlock(err_anim, 'statement-list');
    }

}
let state_window_chat = 'open';

async function openWindowChat(iid) {
    state_window_chat = 'open'; //переводим в открытое состояние
    let response = await fetch('/helpdesk/helpdesk_chat/');
    if (response.ok) {
        innerBlock(await response.text(), 'window-block');
        $('body, html').css('overflow', 'hidden');
    }

    innerBlock(loading_anim, 'main-div-chat');

    

    response = await fetch('/helpdesk/helpdesk_chat/?id=' + iid);
    if (response.ok) {
        if (state_window_chat == 'close') {
            return;
        }
        innerBlock(await response.text(), 'window-block');
    }
}

function openWindowLoading() {
    innerBlock(loading_anim, 'window-block');
}

function openWindowAdd() {
    innerBlock(helpdesk_add, 'window-block');
    showHelpdeskFolders();
}

function closeWindowChat() {
    state_window_chat = 'close' //переводим в закрытое состояние
    closeBlock('window-block');
    $('body, html').css('overflow', 'auto');

}

function closeWindowAdd() {
    closeBlock('window-block');
}


//функции отвечающие за создание новой заявки

async function showHelpdeskFolders() {
    //показать список папок
    innerBlock(loading_anim, 'main-div-add', displ=false);
    let folders_response = await fetch('/helpdesk/helpdesk_folders/');
    if (folders_response.ok) {
        let folders_html = await folders_response.text();
        innerBlock(folders_html, 'main-div-add', displ=false);
    }

}

async function showHelpdeskUsers(iid) {
    //показать список пользователей
    innerBlock(loading_anim, 'main-div-add', displ=false);
    let folders_response = await fetch('/helpdesk/helpdesk_users/?iid=' + iid);
    if (folders_response.ok) {
        let folders_html = await folders_response.text();
        innerBlock(folders_html, 'main-div-add', displ=false);
    }
}

async function showHelpdeskForm(iid) {
    //показать форму заполнения новой заявки
    innerBlock(loading_anim, 'main-div-add', displ=false);
    let form_resposne = await fetch('/helpdesk/helpdesk_form/?iid=' + iid);
    if (form_resposne.ok) {
        let form_html = await form_resposne.text();
        innerBlock(form_html, 'main-div-add', displ=false);
    }
}

async function sendPost(iid) {
    //функция отправки POST-запроса через carbon-api
    let subj = document.getElementById('subj').value;
    let info = document.getElementById('text-info').value;
    innerBlock(loading_anim, 'main-div-add', displ=false);
    let param_iid = 'iid=' + encodeURIComponent(iid);
    let param_subj = '&subj=' + encodeURIComponent(subj);
    let param_info = '&info=' + encodeURIComponent(info);
    let form_resposne = await fetch('/helpdesk/create/?' + param_iid + param_subj + param_info);
    if (form_resposne.ok) {
        let form_html = await form_resposne.text();
        innerBlock(form_html, 'main-div-add', displ=false);
        closeWindowAdd();
        showHelpDesk();
    }
}

async function closeHelpdesk() {
    //функция закрытия заявок
    let url_string = '/helpdesk/close/?';
    let helpdesk_closing_lst = [];
    let checkbox_lst = document.getElementsByClassName('checkbox')
    for (let i=0; i < checkbox_lst.length; i++) {
        let helpdesk_iid = checkbox_lst[i].id;
        let checkbox_state = checkbox_lst[i].checked;
        if (checkbox_state) {
            helpdesk_closing_lst.push(['id'+i, helpdesk_iid]);
        }
    }
    if (!helpdesk_closing_lst.length) {
        alert('Ни одна из заявок не выбрана');
        return;
    }
    url_string += new URLSearchParams(helpdesk_closing_lst);
    innerBlock(loading_anim, 'statement-list');
    let response = await fetch(url_string);
    if (response.ok) {
        await response.text();
    }
    showHelpDesk();
}

async function sendMsg(iid, redirect=false) {
    //функция отправки сообщения в helpdesk
    let text = document.getElementsByClassName('input-msg')[0];
    if (!text.value) {
        alert('Поле ввода пустое');
        return;
    }
    innerBlock(loading_anim, 'main-div-chat');
    let param_iid = 'iid=' + encodeURIComponent(iid);
    let param_text = '&text=' + encodeURIComponent(text.value);
    let send_resposne = await fetch('/helpdesk/send/?' + param_iid + param_text);
    if (send_resposne.ok) {
        let resp = await send_resposne.text();
        if (redirect) {
            location.reload();
            console.log('reload')
        } else {
            openWindowChat(iid);
            
        }
        
    }
}


//точка входа
loadAllModules(showHelpDesk);


