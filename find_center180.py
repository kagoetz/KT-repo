def find_center180(x1,y1,x3,y3):
    slope=(y3-y1)/(x3-x1)
    xc=(x1+x3)/2
    yc=(y1+y3)/2
    dist=m.sqrt(((y3-y1)**2)+((x3-x1)**2))
    r=dist/2
    dst=m.sqrt(((yc-y1)**2)+((xc-x1)**2))
    return[xc,yc,r,dst]