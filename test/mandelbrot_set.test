def in_mandelbrot(x0 : float, y0 :  float, n : int):bool {
    x  = 0.0
    y  = 0.0
    xtemp = 0.0
    while n > 0 {
        xtemp = x*x - y*y + x0
        y = 2.0*x*y + y0
        x = xtemp
        n = n - 1
        if x*x + y*y > 4.0 {
            return 1 == 0
        }
    }
    return 0 == 0
}

def mandel():int {
    xmin = -2.0
    xmax = 1.0
    ymin = -1.5
    ymax = 1.5
    width = 80.0
    height = 40.0
    threshhold = 1000
    dx = (xmax - xmin)/width
    dy = (ymax - ymin)/height

     y  = ymax
     x  = 0.0

     while y >= ymin {
         x = xmin
         while x < xmax {
             if in_mandelbrot(x,y,threshhold) {
                printf('*')
             } else {
                printf('.')
             }
             x = x + dx
         }
         printf('\n')
         y = y - dy
     }
     return 0
}

def main() : int {
    return mandel()
}
