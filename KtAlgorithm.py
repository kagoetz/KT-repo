from xlrd import open_workbook,XL_CELL_TEXT
import math as m
import numpy as np
import xlsxwriter
import shutil
import os

#Must be in a directory that has a "data_entry" xlsx file and a "Logs" folder

#Reads data points from excel spreadsheet and appends to data list
book = open_workbook('data_entry.xlsx')
sheet = book.sheet_by_index(0)
cell = sheet.cell(0,8)
data=[]
for i in range(sheet.nrows):
    data.append(sheet.cell_value(i,8))
CCD_pos=[2214269-1374000,2214269]

#Retrieve data from the data list and convert pixels to microns (each pixel is 12 microns)
#Circle 1 is created by the CCD at the closer location
c1_x0=data[0]*12
c1_y0=data[1]*12
c1_x1=data[2]*12
c1_y1=data[3]*12
c1_x2=data[4]*12
c1_y2=data[5]*12

#Circle 2 is created by the CCD at the farther location
c2_x0=data[6]*12
c2_y0=data[7]*12
c2_x1=data[8]*12
c2_y1=data[9]*12
c2_x2=data[10]*12
c2_y2=data[11]*12

#Retrieve z positions from CCD position list
z1=CCD_pos[0]
z2=CCD_pos[1]

#functions
def circle_center_x(x_0, x_1, x_2, y_0, y_1, y_2):
    #finds the x coordinate of the center of a circle given 3 points on the circle
    m_a = (y_1-y_0)/(x_1-x_0)
    m_b = (y_2-y_1)/(x_2-x_1)
    center_x = (m_b*(x_1+x_0) + (m_a*m_b*(y_0-y_2)) - m_a*(x_2+x_1))/(2*(m_b-m_a))
    return center_x

def circle_center_y(center_x, x_0, x_1, y_0, y_1):
	#finds the y coordinate of the center of a circle given 
	#2 points on the circle and the x coordinate of the circle center
    m_a = (y_1-y_0)/(x_1-x_0)
    y = (-1/m_a)*(center_x - ((x_1+x_0)/2)) + ((y_1+y_0)/2)
    return y

def get_angle(rise,run):
	#finds the angle given the opposite (rise) and adjacent (run) sides of the triangle
    angle=m.degrees(m.atan(abs(rise)/abs(run)))
    return angle                      

def circle_radius(x_0, y_0, center_x, center_y):
	#finds the radius of the circle given the coordinates one point on the circle and the center
    radius = m.sqrt((x_0-center_x)**2+(y_0-center_y)**2)
    return radius

def get_y_intercept(x1,y1,x2,y2):
    #gives "vertical" axis intercept
    yint = y1-(((y2-y1)/(x2-x1))*x1)
    return yint

def get_x_intercept(x1,y1,x2,y2):
	#gives the intercept of the line on the horizontal axis, most typically z-axis
    yint = y1-(((y2-y1)/(x2-x1))*x1)
    xint = ((x2-x1)/(y2-y1))*(-yint)
    return xint

def round_to_n(x, n):
	#rounds x to a defined n number of significant digits
    if not x: return 0
    power = -int(m.floor(m.log10(abs(x)))) + (n - 1)
    factor = (10 ** power)
    return round(x * factor) / factor

def find_center90(x1,y1,x2,y2): 
	#uses 2 points on the circle, given that they are 90 degrees apart,
	#to find the center x and y coordinates and radius in a list
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
    return [xc,yc,r]

def find_center180(x1,y1,x3,y3):
	#uses 2 points on the circle, given that they are 180 degrees apart,
	#to find the center x and y coordinates and radius in a list
    slope=(y3-y1)/(x3-x1)
    xc=(x1+x3)/2
    yc=(y1+y3)/2
    dist=m.sqrt(((y3-y1)**2)+((x3-x1)**2))
    r=dist/2
    dst=m.sqrt(((yc-y1)**2)+((xc-x1)**2))
    return[xc,yc,r]

def rev_to_line(revs,knob):
    #gives lines to pass on the knob after full revolutions (describes the partial revolution)
    revs_dec = (revs-int(revs))
    degrees=revs_dec*360
    # knob=0 if you are working with x or y knob
    if knob==0:
        lines=degrees/21.82
    # knob=1 if you are working with pitch or yaw knob
    if knob==1:
        lines=degrees/15.652
    return(lines)

#Use the functions to characterize the circles

#circle one is the closer circle
#characterizing circle one: all points must be on CCD
center1_x=circle_center_x(c1_x0,c1_x1,c1_x2,c1_y0,c1_y1,c1_y2)
center1_y=circle_center_y(center1_x,c1_x0,c1_x1,c1_y0,c1_y1)
rad1=circle_radius(c1_x0,c1_y0,center1_x,center1_y)

#circle 2 is the farther circle.
#determines whether any of the points are off the CCD (coordinates of 0,0)
#if so, determines which point is, and uses the other two to characterize
#if not, characterizes as above in circle one
if c2_x0==0:
    circle2=find_center90(c2_x2,c2_y2,c2_x1,c2_y1)
    center2_x=circle2[0]
    center2_y=circle2[1]
    rad2=circle_radius(c2_x1,c2_y1,center2_x,center2_y)
elif c2_x1==0:
    circle2=find_center180(c2_x0,c2_y0,c2_x2,c2_y2)
    center2_x=circle2[0]
    center2_y=circle2[1]
    rad2=circle_radius(c2_x0,c2_y0,center2_x,center2_y)
elif c2_x2==0:
    circle2=find_center90(c2_x0,c2_y0,c2_x1,c2_y1)
    center2_x=circle2[0]
    center2_y=circle2[1]
    rad2=circle_radius(c2_x0,c2_y0,center2_x,center2_y)
else:
    center2_x=circle_center_x(c2_x0,c2_x1,c2_x2,c2_y0,c2_y1,c2_y2)
    center2_y=circle_center_y(center2_x,c2_x0,c2_x1,c2_y0,c2_y1)
    rad2=circle_radius(c2_x0,c2_y0,center2_x,center2_y)

#prints characteristicsm as well as variables formatted to copy to matlab visualization
print("Circle one is centered at ("+ str(center1_x) + "," + str(center1_y) + ") and has a radius of " + str(rad1)+".\n")
print("Circle two is centered at ("+ str(center2_x) + "," + str(center2_y) + ") and has a radius of " + str(rad2)+".\n")
print("c1_x0="+str(c1_x0)+"\n"+"c1_y0="+str(c1_y0))
print("c1_x1="+str(c1_x1)+"\n"+"c1_y1="+str(c1_y1))
print("c1_x2="+str(c1_x2)+"\n"+"c1_y2="+str(c1_y2))
print("c2_x0="+str(c2_x0)+"\n"+"c2_y0="+str(c2_y0))
print("c2_x1="+str(c2_x1)+"\n"+"c2_y1="+str(c2_y1))
print("c2_x2="+str(c2_x2)+"\n"+"c2_y2="+str(c2_y2))
print("center1_x="+str(center1_x)+"\ncenter1_y="+str(center1_y))
print("center2_x="+str(center2_x)+"\ncenter2_y="+str(center2_y))
print("rad1="+str(rad1)+"\nrad2="+str(rad2))

#Redefine coordinates relative to the "true" z-axis passing through the center of both circles
c1_x0-=center1_x
c1_x1-=center1_x
c1_x2-=center1_x
c1_y0-=center1_y
c1_y1-=center1_y
c1_y2-=center1_y
c2_x0-=center2_x
c2_x1-=center2_x
c2_x2-=center2_x
c2_y0-=center2_y
c2_y1-=center2_y
c2_y2-=center2_y
 
#finds where laser intersects with X axis in XZ plane, returns dx 
dx=get_y_intercept(z1,c1_x0,z2,c2_x0)

#finds where laser intersects with Y axis in YZ plane, returns dy
dy=get_y_intercept(z1,c1_y0,z2,c2_y0)

#finds where laser intersects with Z axis in XZ plane, returns z coordinate
z_xz=get_x_intercept(z1,c1_x0,z2,c2_x0)

#finds where laser intersects with Z axis in YZ plane, returns z coordinate
z_yz=get_x_intercept(z1,c1_y0,z2,c2_y0)

#finds angle between laser and Z axis in XZ plane, returns yaw 
yaw=get_angle(dx,z_xz)

#finds angle between laser and Z axis in YZ plane, returns pitch 
pitch=get_angle(dy,z_yz)


#translational displacement
#note: spec on laser - one x- or y-knob revolution translates laser 254 microns
xturns=abs(dx/254)
yturns=abs(dy/254)

#round values to 6 sig figs
dx=round_to_n(dx,6)
dy=round_to_n(dy,6)
xturns=round_to_n(xturns,6)
yturns=round_to_n(yturns,6)

#finds the number of lines to pass on each knob for the required partial revolution
linesx=round_to_n(rev_to_line(xturns,0),6)
linesy=round_to_n(rev_to_line(yturns,0),6)

if dx>0:
    #laser is shifted to the left, and needs to be moved to the right, so knob needs to turn left
    xshift="left"
    xdir="left"
    print("The laser is "+str(dx)+" microns to the left of the central axis.")
    print("Turn the X knob " + str(xturns) + " revolutions to the left.")
    print("Pass " + str(linesx) + " lines on x knob.\n")
else:
    #laser is shifted to the right, and needs to be moved to the left, so knob needs to turn right
    xshift="right"
    xdir="right"
    print("The laser is "+str(abs(dx))+" microns to the right of the central axis.")
    print("Turn the X knob " + str(xturns) + " revolutions to the right.")
    print("Pass " + str(linesx) + " lines on x knob.\n")

if dy>0:
    #laser is above centerline, and needs to be moved downward to decrease its y-value. knob turns to the right
    yshift="above"
    ydir="right"
    print("The laser is "+str(dy)+" microns to the above the central axis.")
    print("Turn the Y knob " + str(yturns) + " revolutions to the right.")
    print("Pass " + str(linesy) + " lines on y knob.\n")
else:
    #laser is below centerline, and needs to be moved upward to increase its y-value. knob turns to the left
    yshift="below"
    ydir="left"
    print("The laser is "+str(abs(dy))+" microns to the below the central axis.")
    print("Turn the Y knob " + str(yturns) + " revolutions to the left.")
    print("Pass " + str(linesy) + " lines on y knob.\n")

#angular displacement
#knob spec - 1 revolution is 8mrad of angular displacement
yawturns=yaw/(.008*180/m.pi)
pitchturns=pitch/(.008*180/m.pi)

#round values to 6 sig figs
yaw=round_to_n(yaw,6)
pitch=round_to_n(pitch,6)
yawturns=round_to_n(yawturns,6)
pitchturns=round_to_n(pitchturns,6)

#finds the number of lines to pass on each knob for the required partial revolution
linespitch=round_to_n(rev_to_line(pitchturns,1),6)
linesyaw=round_to_n(rev_to_line(yawturns,1),6)

if c1_x0<c2_x0:
    #laser is pointing to the right. the laser needs to be angled to the left to align with center. Move yaw knob to the right
    yawshift="right"
    yawdir="right"
    print("The laser is angled "+str(yaw)+" degrees to the right of the central axis.")
    print("Turn the yaw knob " + str(yawturns) + " revolutions to the right.")
    print("Pass " + str(linesyaw) + " lines on yaw knob.\n")
if c1_x0>c2_x0:
    #laser is pointing to the left. the laser needs to be angled to the right to align with center. Move yaw knob to the left
    yawshift="left"
    yawdir="left"
    print("The laser is angled "+str(yaw)+" degrees to the left of the central axis.")
    print("Turn the yaw knob " + str(yawturns) + " revolutions to the left.")
    print("Pass " + str(linesyaw) + " lines on yaw knob.\n")  
if c1_y0<c2_y0:
    #laser is pointing upward. the laser needs to be angled to the down to align with center. Move pitch knob to the right
    pitchshift="up"
    pitchdir="right"
    print("The laser is angled "+str(pitch)+" degrees to the up with respect to the central axis.")
    print("Turn the pitch knob " + str(pitchturns) + " revolutions to the right.")
    print("Pass " + str(linespitch) + " lines on pitch knob.\n")
if c1_y0>c2_y0:
    #laser is pointing downward. the laser needs to be angled to the up to align with center. Move pitch knob to the left
    pitchshift="down"
    pitchdir="left"
    print("The laser is angled "+str(pitch)+" degrees to the down with respect to the central axis.")
    print("Turn the pitch knob " + str(pitchturns) + " revolutions to the left.")
    print("Pass " + str(linespitch) + " lines on pitch knob.\n")


#What adjustment is this
adjustment=1

# Create a workbook and add a worksheet.
workbook = xlsxwriter.Workbook("adjust_log_"+str(adjustment)+".xlsx")
sheet1 = workbook.add_worksheet()

#Compile variables for export into a list
results=[dx,xshift,xturns,xdir,dy,yshift,yturns,ydir,yaw,yawshift,yawturns,yawdir,pitch,pitchshift,pitchturns,pitchdir]

# Write data headers.
sheet1.write('A1', "Adjustment No.")
sheet1.write('B1', "Dx")
sheet1.write('C1', "X Shifted to")
sheet1.write('D1', "X Turns")
sheet1.write('E1', "X Turn to")
sheet1.write('F1', "Dy")
sheet1.write('G1', "Y Shifted to")
sheet1.write('H1', "Y Turns")
sheet1.write('I1', "Y Turn to")
sheet1.write('J1', "Yaw")
sheet1.write('K1', "Yaw Shifted to")
sheet1.write('L1', "Yaw Turns")
sheet1.write('M1', "Yaw Turn to")
sheet1.write('N1', "Pitch")
sheet1.write('O1', "Pitch Shifted to")
sheet1.write('P1', "Pitch Turns")
sheet1.write('Q1', "Pitch Turn to")

#Write variables to correct row (for easier merging of all files in an adjustment session in future)
sheet1.write("A"+str(adjustment+1),adjustment)
sheet1.write("B"+str(adjustment+1), results[0])
sheet1.write("C"+str(adjustment+1), results[1])
sheet1.write("D"+str(adjustment+1), results[2])
sheet1.write("E"+str(adjustment+1), results[3])
sheet1.write("F"+str(adjustment+1), results[4])
sheet1.write("G"+str(adjustment+1), results[5])
sheet1.write("H"+str(adjustment+1), results[6])
sheet1.write("I"+str(adjustment+1), results[7])
sheet1.write("J"+str(adjustment+1), results[8])
sheet1.write("K"+str(adjustment+1), results[9])
sheet1.write("L"+str(adjustment+1), results[10])
sheet1.write("M"+str(adjustment+1), results[11])
sheet1.write("N"+str(adjustment+1), results[12])
sheet1.write("O"+str(adjustment+1), results[13])
sheet1.write("P"+str(adjustment+1), results[14])
sheet1.write("Q"+str(adjustment+1), results[15])
workbook.close()

#Move file into logs folder
shutil.move(os.path.abspath("adjust_log_"+str(adjustment)+".xlsx"), "Logs/")
