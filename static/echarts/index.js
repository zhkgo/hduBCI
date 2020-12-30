var LineChart = function( options ) {

  var data = options.data;
  var canvas = document.getElementById("canvas")
  var context = canvas.getContext( '2d' );

  var rendering = false,
      paddingX = 40,
      paddingY = 40,
      width = 800,
      height = 200
      progress = 0;

  canvas.width = width;
  canvas.height = height;

  var maxValue,
      minValue;

  var y1 = paddingY + ( 0.05 * ( height - ( paddingY * 2 ) ) ),
      y2 = paddingY + ( 0.50 * ( height - ( paddingY * 2 ) ) ),
      y3 = paddingY + ( 0.95 * ( height - ( paddingY * 2 ) ) );
  
  format();
  render();
  
  function format( force ) {

    maxValue = 0;
    minValue = Number.MAX_VALUE;
    // 计算最大值和最小值
    data.forEach( function( point, i ) {
      maxValue = Math.max( maxValue, point.value );
      minValue = Math.min( minValue, point.value );
    } );
    //计算每个点的位置
    data.forEach( function( point, i ) {
      point.targetX = paddingX + ( i / ( data.length - 1 ) ) * ( width - ( paddingX * 2 ) );
      point.targetY = paddingY + ( ( point.value - minValue ) / ( maxValue - minValue ) * ( height - ( paddingY * 2 ) ) );
      point.targetY = height - point.targetY;
  
      if( force || ( !point.x && !point.y ) ) {
        point.x = point.targetX + 30;
        point.y = point.targetY;
        point.speed = 0.04 + ( 1 - ( i / data.length ) ) * 0.05;
      }
    } );
    
  }

  function render() {
    if( !rendering ) {
      requestAnimationFrame( render );
      return;
    }
    context.font = '10px sans-serif';
    context.clearRect( 0, 0, width, height );  //从0，0坐标位置，清空[width, height]大小的矩形
    var progressDots = Math.floor( progress * data.length );
    var progressFragment = ( progress * data.length ) - Math.floor( progress * data.length );
    data.forEach( function( point, i ) {
      if( i <= progressDots ) {
        point.x += ( point.targetX - point.x ) * point.speed;
        point.y += ( point.targetY - point.y ) * point.speed;
        context.save();
        context.restore();
      }
    } );
    context.save();
    context.beginPath();
    context.strokeStyle = '#F00';    // 开始的线的颜色
    context.lineWidth = 1;

    var futureStarted = false;   //开始加入

    data.forEach( function( point, i ) {
      if( i <= progressDots ) {
        var px = i === 0 ? data[0].x : data[i-1].x,
            py = i === 0 ? data[0].y : data[i-1].y;
        var x = point.x,
            y = point.y;
        if( i === progressDots ) {
          x = px + ( ( x - px ) * progressFragment );
          y = py + ( ( y - py ) * progressFragment );
        }
        context.stroke();
        context.beginPath();
        context.moveTo( px, py );
        context.strokeStyle = '#';
        if( i === 0 ) {
          context.moveTo( x, y );
        } else {
          context.lineTo( x, y );
        }
      }
    });
    context.stroke();
    context.restore();
    progress += ( 1 - progress ) * 0.02;
    requestAnimationFrame( render );

  }
  
  this.start = function() {
    rendering = true;
  }
  
  this.stop = function() {
    rendering = false;
    progress = 0;
    format( true );
  }
  
  this.restart = function() {
    this.stop();
    this.start();
  }
  
  this.append = function( points ) {
    data.shift()
    //progress -= points.length / data.length;
    data = data.concat( points );
    format();
  }
  
  this.populate = function( points ) {    
    progress = 0;
    data = points;
    
    format();
  }

};

var chart = new LineChart({ data: [] });

var arrs = []
for (var i=0; i<3000; i++) {
    arrs.push({value: Math.random() * 1500})
}

reset();

chart.start();

function append() {
  chart.append([
    {value: 1300 + ( Math.random() * 1500 )}
  ]);
}

function restart() {
  chart.restart();
}

function reset() {
  chart.populate(arrs);
}
setTimeout(function () {
    for (var i=0; i<1; i++) {
        chart.append([
            {value: 1300 + ( Math.random() * 1500 )}
        ]);
    }
}, 4000)

