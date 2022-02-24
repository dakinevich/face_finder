eel.expose(getVideo);
async function getVideo(){
    let file = await eel.getFirstFrame()();
    if (file != "") {
        setVideoMod();
        document.querySelector(".pattern-video").src = file;
        results = document.querySelectorAll('.result-img');
        results.forEach(res => {
            res.remove();
        });
    }
}

eel.expose(getPhotos);
async function getPhotos(){
    let [inds, files] = await eel.getPatterns()();
    if (inds != []) {
        setPhotoMode();
        inds.forEach((ind, i) => {
            let file = files[i];
            parent = document.querySelector(".pattern-container");
            var child = document.createElement("div");
            child.style.backgroundImage = "url('"+ file +"')";
            child.classList.add("pattern-photo", "anim");
            child.onclick = removeElem;
            child.id = "pattern-" + ind;
            parent.appendChild(child);
        });
    }
}

eel.expose(setVideoMod);
async function setVideoMod(){
    let photo = document.querySelector(".pattern-container");
    photo.style.display = "none";
    let video =  document.querySelector(".pattern-video-container");
    video.style.display = "flex";
}

eel.expose(setPhotoMode);
async function setPhotoMode(){
    let video =  document.querySelector(".pattern-video-container");
    video.style.display = "none";
    let photo = document.querySelector(".pattern-container");
    photo.style.display = "flex";
}

eel.expose(setProgress);
function setProgress(persent){
    var style = document.querySelector('.pattern').style;
    style.setProperty('--progress', persent+'%');
}

eel.expose(getFaces);
async function getFaces(){
    let [inds, files] = await eel.getFaces()();
    if (inds != []) {
        inds.forEach((ind, i) => {
            let file = files[i];
            parent = document.querySelector(".faces-container");
            last = document.querySelector(".face-empty"); 
            var child = document.createElement("div");
            child.style.backgroundImage = "url('"+ file +"')";
            child.classList.add("face-img", "anim");
            child.onclick = removeElem;
            child.id = "face-" + ind;
            parent.insertBefore(child, last);
        });
        
    }
}

eel.expose(removeElem);
async function removeElem(event){
    id = event.target.id;
    await eel.removeById(id)();
    let elem = document.getElementById(id);
    elem.remove();
}

eel.expose(callAnalyze);
function callAnalyze(event){
    makeDisabled();
    results = document.querySelectorAll('.result-img');
        results.forEach(res => {
            res.remove();
    });
    eel.analyze()();
}

eel.expose(makeDisabled);
function makeDisabled(){
    document.querySelector(".pattern-video-btn").classList.add("btn-disable")
    document.querySelector(".pattern-photos-btn").classList.add("btn-disable")
    document.querySelector(".face-empty").classList.add("btn-disable")
    document.querySelector(".result-btn").classList.add("btn-disable")
    document.querySelector(".save-btn").classList.add("btn-disable")
}

eel.expose(makeEnable);
function makeEnable(){
    document.querySelector(".pattern-video-btn").classList.remove("btn-disable")
    document.querySelector(".pattern-photos-btn").classList.remove("btn-disable")
    document.querySelector(".face-empty").classList.remove("btn-disable")
    document.querySelector(".result-btn").classList.remove("btn-disable")
    document.querySelector(".save-btn").classList.remove("btn-disable")
}

eel.expose(callSave);
function callSave(){
    eel.saveFaces()();
}

eel.expose(setNewResult);
function setNewResult(img_src){
    parent = document.querySelector(".result-container");
    var child = document.createElement("div");
    child.style.backgroundImage = "url('"+ img_src +"')";
    child.classList.add("result-img");
    parent.appendChild(child);
}

eel.expose(alertMsg);
function alertMsg(msg) {
    alert(msg);
}

document.addEventListener("DOMContentLoaded", async function(event) {
    console.log("DOM fully loaded and parsed");
    let [inds, files, frame_file, results] = await eel.DOM_update()();
    if (typeof(frame_file) == "string") {
        if (frame_file != "") {
            document.querySelector(".pattern-video").src = frame_file;
        }
    }
    else {
        setPhotoMode();
        let [inds, files] = frame_file;
        inds.forEach((ind, i) => {
            let file = files[i];
            parent = document.querySelector(".pattern-container");
            var child = document.createElement("div");
            child.style.backgroundImage = "url('"+ file +"')";
            child.classList.add("pattern-photo", "anim");
            child.onclick = removeElem;
            child.id = "pattern-" + ind;
            parent.appendChild(child);
        });
    }
    inds.forEach((ind, i) => {
        let file = files[i];
        parent = document.querySelector(".faces-container");
        last = document.querySelector(".face-empty"); 
        var child = document.createElement("div");
        child.style.backgroundImage = "url('"+ file +"')";
        child.classList.add("face-img", "anim");
        child.onclick = removeElem;
        child.id = "face-" + ind;
        parent.insertBefore(child, last);
    });
    results.forEach(res => {
        setNewResult(res);
    })
  });
