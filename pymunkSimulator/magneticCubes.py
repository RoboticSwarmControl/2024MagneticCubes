#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 08:58:11 2022
 
  make cubes with embedded magnets that interact.
  This demo will place cubes at the mouse position.  They will have magnets to pull them.
  Then pressing keyboard will change the pivot point of the cubes
  then arrow keys will change the orientation of the global magnetic field.
  [Done] cubes that walk and stick together.
  [DONE]  tune forces and friction so that dominos turn together.    -- was problem with the forces
  [DONE]  make two species of robot, red and blue
  [DONE]  determine that when blocks connect and redefine as a polyomino.  Will need a data structure of all the magnets and the polyomino shape.
  [DONE]  Set new N and S friction points.
  [DONE]  Bang-bang is less stable than simple ramps in velocity.  I could also try SmootherStep()
  [DONE] Made a controller to apply some pivot steps
    
   # the system gets unstable when it pivots.  Maybe I need to convvert the shapes to rigid bodies when I pivot?
 
    # make a controller to steer:  connectEdges(CubeA,SideA,CubeB,SideB)
    # make initializer that makes a new world with cubes and polyominos
    # make a way to save the system state (magnetic field orientation, the pose of all cubes, and the location of all magnets.)

# https://www.pymunk.org/en/latest/pymunk.html    Example of a callback that limits the velocity:????

@author: Aaron T Becker
"""
import pygame
import pymunk
import pymunk.pygame_util
import math


pygame.init()

WIDTH, HEIGHT = 800, 800
window = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("magnetic cube simulator")
MRAD =15  #distance of magnet from center of cube
rad = 20 #half length of side of cube

def draw(space, window, draw_options,cubes,magAngle,magConnect,poly):
    RED = (255, 0, 0,100)
    GREEN = (0, 255, 0,100)
    BLACK = (0, 0, 0,100)
    LIGHTBROWN = (196, 164, 132,100)
    #YELLOW = (255,255,0,100)
    #https://sashamaps.net/docs/resources/20-colors/
    sashaColors = ((230, 25, 75,100), (60, 180, 75,100), (255, 225, 25,100), (0, 130, 200,100), (245, 130, 48,100), (145, 30, 180,100), (70, 240, 240,100), (240, 50, 230,100), (210, 245, 60,100), (250, 190, 212,100), (0, 128, 128,100), 
                (220, 190, 255,100), (170, 110, 40,100), (255, 250, 200,100), (128, 0, 0,100), (170, 255, 195,100), (128, 128, 0,100), (255, 215, 180,100), (0, 0, 128,100), (128, 128, 128,100), (255, 255, 255,100), (0, 0, 0,100))
    window.fill("white" )

    space.debug_draw(draw_options)
    
    # draw the magnets and CenterOfGravity-- for all cubes
    for cube in cubes: #COM
        pygame.draw.circle(window, BLACK,  cube.body.local_to_world(cube.body.center_of_gravity), 7)
    
    for cube in cubes:
        #magnets
        for i, magP in enumerate(cube.magnetPos):
            if 0< magP[0]*cube.magnetOri[i][0]+magP[1]*cube.magnetOri[i][1]:
                magcolor = GREEN
            else:
                magcolor = RED
            pygame.draw.circle(window, magcolor,  cube.body.local_to_world(magP) , 5)
            
    #draw the connections
    for i,connects in enumerate(magConnect):
        for j in connects:
            pygame.draw.line(window, sashaColors[poly[i]], cubes[i].body.local_to_world((0,0)), cubes[j].body.local_to_world((0,0)),3)
            #pygame.draw.line(window, "yellow", cubes[i].body.local_to_world((0,0)), cubes[j].body.local_to_world((0,0)),3)
            #pygame.draw.circle(window, YELLOW,  cubes[i].body.local_to_world, 6)
       
    # draw the compass  
    pygame.draw.circle(window, LIGHTBROWN,  (10,10), 11)
    pygame.draw.line(window, "red",   (10,10), (10+10*math.cos(magAngle), 10+10*math.sin(magAngle)) ,3) 
    pygame.draw.line(window, "green", (10,10), (10-10*math.cos(magAngle), 10-10*math.sin(magAngle)) ,3) 
    
    pygame.display.update() #draw to the screen
    
def create_cube(space, pos, magAngle, cubetype):
    LIGHTBROWN = (196, 164, 132,100)
    #LIGHTGREEN = (205, 255, 205,100)
    #LIGHTRED   = (255, 205, 205,100)

    body = pymunk.Body()
    body.position = pos
    shape = pymunk.Poly(body, [(-rad,-rad),(-rad,rad),(rad,rad),(rad,-rad)],radius = 1)
    #shape = pymunk.Poly.create_box(body,(2*rad,2*rad), radius = 1)
    shape.mass = 10
    shape.elasticity = 0.4
    shape.friction = 0.4
    shape.color = LIGHTBROWN

    shape.magnetPos = [(MRAD,0),(0,MRAD),(-MRAD,0),(0,-MRAD)]
    if cubetype ==0:
        shape.magnetOri = [(1,0),(0,1),(1,0),(0,-1)]
    else:
        shape.magnetOri = [(1,0),(0,-1),(1,0),(0,1)]
    body.angle = magAngle
    space.add(body,shape)

    return shape
  

def calculate_distance(p1,p2):
    return math.sqrt( (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2  )

def calculate_norm(p):
    return math.sqrt( p[1]**2 + p[0]**2  )

def calculate_angle(p1,p2):
    return math.atan2((p2[1]-p1[1]),     (p2[0]-p1[0])  )

def rotateVecbyAng(vec, ang):  #rotate a vector in 2D by angle ang
    (x,y) = vec
    return ( math.cos(ang)*x - math.sin(ang)*y, math.sin(ang)*x + math.cos(ang)*y)
    
def create_boundaries(space, width, height):
    rects = [
        [(width/2, height - 10),(width, 20)],
        [(width/2,  10),(width, 20)],
        [(10,  height/2),(20, height)],
        [(width-10,  height/2),(20, height)]
    ]
    for pos, size in rects:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = pos
        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.4
        shape.friction = 0.5
        space.add(body,shape)
     
def magForce1on2( p1, p2, m1,m2): #https://en.wikipedia.org/wiki/Magnetic_moment 
    #rhat = unitvector pointing from magnet 1 to magnet 2 and r is the distance
    r = calculate_distance(p1,p2)
    if r < 2*(rad-MRAD):
        r = 2*(rad-MRAD)  #limits the amount of force applied
        
    rhat  = ((p2[0]-p1[0])/r, (p2[1]-p1[1])/r) #r̂ is the unit vector pointing from magnet 1 to magnet 2 
    
    m1r   = m1[0]*rhat[0] + m1[1]*rhat[1]  #m1 dot rhat
    m2r   = m2[0]*rhat[0] + m2[1]*rhat[1]  #m2 dot rhat
    m1m2  = m1[0]*m2[0]   + m1[1]*m2[1]     #m1 dot m2
    
    #print(repr([r,rhat,m1r,m2r,m1m2]))
    sc = 20000000
    
    f = (sc*1/r**4 * (m2[0]*m1r + m1[0]*m2r + rhat[0]*m1m2 - 5*rhat[0]*m1r*m2r),   
         sc*1/r**4 * (m2[1]*m1r + m1[1]*m2r + rhat[1]*m1m2 - 5*rhat[1]*m1r*m2r))
    #print( "force is " + repr(f) )
    #print(repr(f) )
    return f

def detectPoly(cubes, magConnect):
    poly = list(range(0, len(cubes)))  #the unique polygon each cube belongs to.
    
    for i,cubei in enumerate(cubes):
        for j,cubej in enumerate(cubes,i):   #for j,cubej in enumerate(cubes,i):
            #check to see if they are magnetically connected
            if magConnect[i].count(j)>0:
                #if so, assign them to the same poly
                piS = poly[i]
                pjS = poly[j]
                minP = min(piS,pjS)
                poly[j] = minP
                poly[i] = minP
                if piS != pjS:
                    maxP = max(piS,pjS)
                    for k in range(len(cubes)):  # never gets called!
                        if poly[k] == maxP:
                            #print("Found equiv")
                            poly[k] = minP #assign all polys that have pjS or piS to be the minimum value
    
    polyset = list(set(poly))  # unique ID numbers
    #print("poly = " + repr(poly))
    #print("polyset = " + repr(polyset))
    
    newIndices = list(range(len(polyset))) #how many IDs there are
    for i in newIndices:     # renumber the polys poly = [0,0,1,3,3,8,8,8] --> [0,0,1,2,2,3,3,3] 
        poly = [i if item == polyset[i] else item for item in poly]                        
    #print("poly = " + repr(poly))
    return poly

# def rotateToHeading( ang0, angGoal, duration, fps):
#     #apply a bang-bang transition: returns a sequence of magAngle to follow to transfer from ang0 to angGoal in duration seconds
#     angDelta = math.atan2( math.sin(angGoal-ang0), math.cos(angGoal-ang0) ) #computes the shortest angle from ang0 to angGoal
#     tHalf = duration/2 #time to hold acceleration before switching.
#     steps = math.ceil(duration*fps)
#     acc = 4*angDelta/(duration*duration)
    
#     if angDelta >0:
#         angDeltaSign = 1
#     else:
#         angDeltaSign = -1
#     angs = [0 for _ in range(steps)]
    
#     for k in range(steps):
#         t = k/fps
#         if t <= tHalf:
#             offset = angDeltaSign*1/2*acc*t**2;
#         elif t <= tHalf*2:
#             offset = angDeltaSign*(1/2*acc*tHalf**2 + acc*tHalf*(t-tHalf) - 1/2*acc*(t-tHalf)**2);
#         else:
#             offset = angDelta
#         angs[k] = ang0 + offset
#     return angs

def rotateToHeading( ang0, angGoal, duration, fps):
    #apply a linear ramp transition: returns a sequence of magAngle to follow to transfer from ang0 to angGoal in duration seconds
    angDelta = math.atan2( math.sin(angGoal-ang0), math.cos(angGoal-ang0) ) #computes the shortest angle from ang0 to angGoal
    steps = math.ceil(duration*fps)
    angs = [0 for _ in range(steps)]
    for k in range(steps):
        t = k/fps
        if t <= duration:
            offset = angDelta*t/duration;
        else:
            offset = angDelta
        angs[k] = ang0 + offset
    return angs
        
    
def pivotWalkR( ang0, numberOfSteps, pivotAngle, fps):
    # takes numberOfSteps in the forward direction, pivoting pivotAngle each stride, ending with the original orientation
    #a step is a full pivot on each side.  First step is about the right side (elevation 1)
    #take a half step backwards
    angCur = ang0
    eleCur = 1
    duration = 2
    angs = []
    elevs = []
    for i in range(2*numberOfSteps+1):
        angChange = pivotAngle
        if i==0 or i == 2*numberOfSteps:
            angChange = pivotAngle/2
        if i%2 == 0:
            eleCur = 1
        else:
            eleCur = -1
            angChange *=-1
            
        angsN = rotateToHeading( angCur, angCur+angChange, duration, fps)
        angCur+=angChange  #update the angle
        angs +=angsN
        elevs+=[eleCur for _ in range(len(angsN))]
        #stop the robot for a bit
        angs += [angCur for _ in range(15)]
        elevs+= [0 for _ in range(15)]
        
    #print("Angs  = "+repr(angs))
    #print("elevs = "+repr(elevs))
    return (angs,elevs)    
        

def updatePivots(cubes, poly, magElevation):
    #updates the COM
    if magElevation == 0:
        for cube in cubes:
            cube.body.center_of_gravity = ( 0, 0)
            pos = cube.body.position
            cube.body.position = (pos[0],pos[1]) #for some reason you need to assign this new position or it will jump when the COG is moved.
    else:
        myInf = 100000
        centroids = [[0,0] for _ in range(max(poly)+1)]
        if magElevation > 0:
            minXyLyR = [[ myInf, 0, 0] for _ in range(max(poly)+1)]
            for i,cubei in enumerate(cubes):
                polyi = poly[i]
                #change everything into local coordinate frame of cube[0]
                (cx,cy) = cubes[0].body.world_to_local(cubei.body.local_to_world((-MRAD,0)) )
                if round(cx/rad) < round(minXyLyR[polyi][0]/rad):
                    minXyLyR[polyi] = [cx,cy,cy] #this is the minimum row, so it is the pivot
                elif round(cx/rad) == round(minXyLyR[polyi][0]/rad):
                    if round(cy/rad) < round(minXyLyR[polyi][1]/rad):
                        minXyLyR[polyi][1] = cy
                    elif round(cy/rad) > round(minXyLyR[polyi][2]/rad):
                        minXyLyR[polyi][2] = cy
            myYxLxR = minXyLyR
        else:
            maxXyLyR = [[-myInf, 0, 0] for _ in range(max(poly)+1)]
            for i,cubei in enumerate(cubes):
                polyi = poly[i]
                #change everything into local coordinate frame of cube[0]
                (cx,cy) = cubes[0].body.world_to_local(cubei.body.local_to_world((MRAD,0)) )
                if round(cx/rad) > round(maxXyLyR[polyi][0]/rad):
                    maxXyLyR[polyi] = [cx,cy,cy]
                elif round(cx/rad) == round(maxXyLyR[polyi][0]/rad):
                    if round(cy/rad) < round(maxXyLyR[polyi][1]/rad):
                        maxXyLyR[polyi][1] = cy
                    elif round(cy/rad) > round(maxXyLyR[polyi][2]/rad):
                        maxXyLyR[polyi][2] = cy
            myYxLxR = maxXyLyR    
        for i,myYxLxRi in enumerate(myYxLxR):  #calculate the centroids
                centroids[i] = cubes[0].body.local_to_world( (myYxLxRi[0],(myYxLxRi[1]+myYxLxRi[2])/2)  )    
        for i,cubei in enumerate(cubes):  #apply the centroids            
            cubei.body.center_of_gravity = cubei.body.world_to_local( centroids[poly[i]]  )
            pos = cubei.body.position
            cubei.body.position = (pos[0],pos[1]) #for some reason you need to assign this new position or it will jump when the COG is moved.


def run(window, width, height):
    run = True
    clock =  pygame.time.Clock()
    fps = 60
    dt = 1/fps
    
    space = pymunk.Space()
    space.gravity = (0,0)  # gravity doesn't exist
    space.damping = 0.2  #simulate top-down gravity with damping
    magAngle = 0  #orientation of magnetic field (in radians)
    magElevation = 0 
    fmag = 1000
    create_boundaries(space, width, height)
    cubes = []  #our magnetic cubes

    draw_options = pymunk.pygame_util.DrawOptions(window)
    pressed_pos = None  
    cubetype = 0;  # currently type 0 and 1 are supported
    connectionForceMin = calculate_norm(magForce1on2( (0,0), (0,2*(rad-MRAD)+5 ), (0,1), (0,1)))  #NS connection

    #controllers:
    controlStep = 0
    controlActive = False
    controlAngs = []
    controlElevs= []

    while run:
        
        #apply the controller
        if controlActive:
            if controlStep<len(controlAngs):
                magAngle = controlAngs[controlStep]
                magElevation = controlElevs[controlStep]
                controlStep +=1
            else:
                controlActive = False
        
        # zero out the connections
        magConnect = [ [] for _ in range(len(cubes)) ]
        # Apply forces from magnets
        for i,cubei in enumerate(cubes):
            angi = cubei.body.angle
            # Apply forces from magnet field  (torques)
            cubei.body.apply_force_at_local_point( (0,-math.sin(angi-magAngle)*fmag)  , ( MRAD, 0)  )
            cubei.body.apply_force_at_local_point( (0, math.sin(angi-magAngle)*fmag)  , (-MRAD, 0)  )
             # Apply forces from the magnets on other cubes
            for j,cubej in enumerate(cubes):
                if i<=j:
                    continue
                angj = cubej.body.angle
                if calculate_distance(cubei.body.position, cubej.body.position) <= 4*rad:
                    
                     for k, pikL in enumerate(cubei.magnetPos):
                         for n, pjnL  in enumerate(cubej.magnetPos):
                             pik = cubei.body.local_to_world( pikL  )
                             mik = rotateVecbyAng(cubei.magnetOri[k] , angi)
                             #(xk,yk) = cubei.magnetOri[k] (xk,yk) = cubei.magnetOri[k] 
                             #mik = ( math.cos(angi)*xk - math.sin(angi)*yk, math.sin(angi)*xk + math.cos(angi)*yk)
                             pjn = cubej.body.local_to_world( pjnL  )
                             mjn = rotateVecbyAng(cubej.magnetOri[n], angj)
                             #(xn,yn) = cubej.magnetOri[n]
                             #mjn = ( math.cos(angj)*xn - math.sin(angj)*yn, math.sin(angj)*xn + math.cos(angj)*yn)
                             fionj = magForce1on2( pik, pjn, mik, mjn )  # magForce1on2( p1, p2, m1,m2)
                             cubei.body.apply_force_at_world_point( (-fionj[0],-fionj[1]) , pik  )
                             cubej.body.apply_force_at_world_point(  fionj ,                pjn  )
                             if calculate_norm(fionj)>connectionForceMin:
                                 magConnect[i].append(j)
                                 magConnect[j].append(i)
                         

        poly = []
        if len(cubes)>0:
            poly = detectPoly(cubes, magConnect)         #detect polyominos
        #place the pivot point to match the polyominoes
        updatePivots(cubes, poly, magElevation)

        #print(magConnect)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                print(event.key)
                if event.key == 119:  #'w'
                    cubetype = 1-cubetype
                    print("Cube type is now " + repr(cubetype))
                if event.key == 101:  #'e'
                    controlAngs = rotateToHeading( magAngle, magAngle+math.pi/2, 2, fps)
                    controlElevs = [magElevation for _ in controlAngs  ]
                    controlStep = 0
                    controlActive = True
                if event.key == 102:  #'f'
                    (controlAngs,controlElevs) = pivotWalkR( magAngle, 3, math.pi/16, fps)
                    controlStep = 0
                    controlActive = True
                    
                if event.key == 97:  #'a'
                    magElevation = 1       
                if event.key == 115: #'s'
                    magElevation = 0
                if event.key == 100: #'d'
                    magElevation = -1
 
                 
                if event.key == pygame.K_LEFT:
                        magAngle -= math.pi/6
                if event.key == pygame.K_RIGHT:
                        magAngle += math.pi/6
            if event.type == pygame.QUIT:
                run = False
                break
            if event.type == pygame.MOUSEBUTTONDOWN:
                pressed_pos = pygame.mouse.get_pos()
                cubes.append(  create_cube(space, pressed_pos, magAngle, cubetype) )
                        
            
        draw(space, window,draw_options,cubes,magAngle,magConnect,poly)
        space.step(dt)  # how fast the simshould go
        clock.tick(fps)
        
    pygame.quit()
        
if __name__ == "__main__":
    run(window,WIDTH, HEIGHT)
