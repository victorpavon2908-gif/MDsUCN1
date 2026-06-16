const ctx = document.getElementById("chart");


new Chart(ctx, {

type:"doughnut",

data:{

labels:[
"Brasil",
"España",
"Argentina",
"Francia"
],


datasets:[{

data:[
35,
25,
20,
20
],


backgroundColor:[

"#009c3b",
"#c60b1e",
"#75aadb",
"#0055a4"

]


}]


},


options:{


responsive:true,


plugins:{

legend:{

position:"bottom"

}


}


}


});