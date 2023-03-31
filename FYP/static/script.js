fetch("https://eonet.gsfc.nasa.gov/api/v3/categories/severeStorms").then((data)=>{
         //console.log(data);
         return data.json();
}).then((objectData)=>{
     console.log(objectData.events[0]);
     console.log(objectData.events[1]);

     for(let i=0;i<objectData.events.length;i++)
     {
      console.log(i);
      var data = objectData.events[i];
      var id = "b"+(i+1);
      var id2 = "t"+(i+1);
      tableData = `<tr>
      <td id="${id2}">${data.title}</td>
      <td>${data.geometry[i].coordinates[1]}</td>
      <td>${data.geometry[i].coordinates[0]}</td>
      <td>${data.geometry[i].magnitudeValue}</td>
      <td><a href=""><button onclick="sendUserInfo(${id})" id="${id}">Predict</button></a></td>
    </tr>`
       document.getElementById("table-body").innerHTML+=tableData;
     }
     var b1 = document.getElementById("b1");
     var b2 = document.getElementById("b2");
     b1.addEventListener("click",function(){
      var title = document.getElementById("t1").innerHTML;
      console.log(title)
     })
     b2.addEventListener("click",function(){
      var title = document.getElementById("t2").innerHTML;
      console.log(title)
     })
     b3.addEventListener("click",function(){
      var title = document.getElementById("t3").innerHTML;
      console.log(title)
     })
     b4.addEventListener("click",function(){
      var title = document.getElementById("t4").innerHTML;
      console.log(title)
     })
     b5.addEventListener("click",function(){
      var title = document.getElementById("t5").innerHTML;
      console.log(title)
     })
})

function runScript(){
  fetch('/run-script')
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log(error))
}

function sendUserInfo(arg)
{
  if(arg==b1)
  {
      var title = document.getElementById("t1").innerHTML;
      console.log(title)
      const request = new XMLHttpRequest()
      request.open('POST',`/run-script/${JSON.stringify(title)}`)
      request.send();
  }
  else if(arg==b2)
  {
      var title = document.getElementById("t2").innerHTML;
      console.log(title)
      const request = new XMLHttpRequest()
      request.open('POST',`/run-script/${JSON.stringify(title)}`)
      request.send();
     }
  else if(arg==b3)
  {
      var title = document.getElementById("t3").innerHTML;
      console.log(title)
      const request = new XMLHttpRequest()
      request.open('POST',`/run-script/${JSON.stringify(title)}`)
      request.send();
     }
  else if(arg==b4)
  {
      var title = document.getElementById("t4").innerHTML;
      console.log(title)
      const request = new XMLHttpRequest()
      request.open('POST',`/run-script/${JSON.stringify(title)}`)
      request.send();
     }
  else if(arg==b5)
  {
      var title = document.getElementById("t5").innerHTML;
      console.log(title)
      const request = new XMLHttpRequest()
      request.open('POST',`/run-script/${JSON.stringify(title)}`)
      request.send();
     }
  }