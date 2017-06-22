def find_center90(x1,y1,x2,y2): 
    slope=(y2-y1)/(x2-x1)
    perp=-1/slope
    xm=(x1+x2)/2
    ym=(y1+y2)/2
    dist=m.sqrt(((y2-y1)**2)+((x2-x1)**2))
    r=dist/(m.sqrt(2))
    d_perp=dist/2
    angl=m.atan(perp)
    dx=d_perp*m.cos(angl)
    dy=d_perp*m.sin(angl)
    xc=xm-dx
    yc=ym-dy
    dst=m.sqrt(((yc-y1)**2)+((xc-x1)**2))
    return [xc,yc,r,dst,xm,ym]
