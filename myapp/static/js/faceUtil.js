var faceUtile ={
      width:500,//图片宽度
      height:500,//图片高度
      isOpen:false ,//是否开启摄像头
      promise:null,
      openVideo:  function (id) { //打开摄像头
          var mythis = this;
          try {
              var oldVideo = document.getElementById("myVideo");
              if (oldVideo && oldVideo.parentNode) oldVideo.parentNode.removeChild(oldVideo);
              var oldCanvas = document.getElementById("myCavans");
              if (oldCanvas && oldCanvas.parentNode) oldCanvas.parentNode.removeChild(oldCanvas);
          } catch (e) {}
          $("#"+id+"").empty();
          let vedioComp = "<video id='myVideo' width='"+this.width+"px' height='"+this.height+"px' autoplay='autoplay' style='margin-top: 0px'></video>" +
              "<canvas id='myCavans' width='"+this.width+"px' height='"+this.height+"px' style='display: none'></canvas>";
          $("#"+id+"").append(vedioComp);
          let constraints = {
              video: {width: mythis.width, height: mythis.height},
              audio: false
          };
          //获得video摄像头区域
          let video = document.getElementById("myVideo");

          this.promise = navigator.mediaDevices.getUserMedia(constraints);
          this.promise.then(function (MediaStream) {
              video.srcObject = MediaStream;
              video.play();

          });
          this.isOpen=true;
      },

    getDecode:function () {//获取图片decode码
          if(this.isOpen){
              let myVideo = document.getElementById("myVideo");
              let myCavans = document.getElementById("myCavans");
              let ctx = myCavans.getContext('2d');
              ctx.drawImage(myVideo, 0, 0, this.width, this.height);
              var decode = myCavans.toDataURL();
              return decode;
          }else{
              alert("没有开启摄像头");

          }

    }
}


