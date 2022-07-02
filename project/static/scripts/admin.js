"use strict";

const DEBUG = true;
const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";

function renderError(jqxhr) {
    let msg = jqxhr.responseJSON["@error"]["@message"];
    $("div.notification").html("<p class='error'>" + msg + "</p>");
}

function renderMsg(msg) {
    $("div.notification").html("<p class='msg'>" + msg + "</p>");
}

function getResource(href, renderer) {

    $.ajax({
        url: href,
        success: renderer,
        error: renderError
    });
}

function sendData(href, method, item, postProcessor) {

    $.ajax({
        url: href,
        type: method,
        data: JSON.stringify(item),
        contentType: PLAINJSON,
        processData: false,
        success: postProcessor,
        error: renderError
    });
}
function followLink(event, a, renderer) {
    event.preventDefault();
    getResource($(a).attr("href"), renderer);
}
function RecipeRow(item) {
    console.log("PWP RRRR RRRRR");
    console.log(item.href);

    let link = "<a href='" +
                item +
                "' onClick='followLink(event, this, renderRecipe)'>view</a>";

    return "<tr><td>" + item.title +
            "</td><td>" + link + "</td></tr>";
}

function appendRecipeRow(body) {
    $(".resulttable tbody").append(RecipeRow(body));
}


function renderRecipe(body) {
    console.log("bbb");

    console.log("vvv", body.title);
    $(".resulttable thead").empty();
    $(".resulttable tbody").empty();
    renderRecipeForm(body["@controls"].edit);
    $("input[name='title']").val(body.title);
    //$("input[name='model']").val(body.model);
    //$(".resulttable thead").html(
    //   "<h3>"+ body.title +"</h3>"
    //);


}
function renderRecipeForm(ctrl) {

    console.log(ctrl);

    let form = $("<form>");
    let title = ctrl.schema.properties.title;

    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    //form.submit(submitSensor);
    //form.append("<label>" + name.description + "</label>");
    //form.append("<input type='text' name='name'>");
    //form.append("<label>" + model.description + "</label>");
    //form.append("<input type='text' name='model'>");
    //ctrl.schema.required.forEach(function (property) {
    //    $("input[name='" + property + "']").attr("required", true);
    //});
    //form.append("<input type='submit' name='submit' value='Submit'>");
    $("div.form").html(form);
}

function renderRecipes(body) {
    console.log("drdrd");

    $("div.navigation").empty();
    $("div.tablecontrols").empty();
    $(".resulttable thead").html(
        "<tr><th>Title</th><th>Actions</th></tr>"
    );
    let tbody = $(".resulttable tbody");

    tbody.empty();
    body.items.forEach(function (item) {
        tbody.append(RecipeRow(item));
    });
    //renderRecipeForm(body["@controls"]);
}


$(document).ready(function () {
    getResource("http://localhost:5000/api/recipes/", renderRecipes);
});
