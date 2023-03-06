function optimalOrientationControlMagneticPoly()
% given a polyomino made of magnet cubes, we want to orient it to a new
% direction as fast as possible.  What is the sequence of magnetic inputs
% we should use?  Currently we tried
% (1) setting the magnetic field to the desired orientation
% (2) using a 'bang-bang' control on magnetic orientation to ramp up the
% angular velocity and then ramp it down to stop at the goal.
% (3) linearly interpolate the magnetic orientation.
% of these, (2) was especially bad because torque =
% mu*beta*sin(MagOrientation - MagnetOrientation).  beta is the magnetic
% moment of one cube, so a device composed of n cubes has torque
% n*mu*beta*sin(MagOrientation - MagnetOrientation)
% Assume that friction is proportional to angular speed.
%
% The inertia of a cuboid is 1/12*mass*(length^2 + width^2) about a
% vertical axis passing through the cuboid's center of mass.
%
% Our cube rotates around one edge.
% By the Parallel Axis theorem, https://en.wikipedia.org/wiki/Parallel_axis_theorem
% Inertia_end = Inertia_centerOfMass + m*d^2, where d is the perpendicular
% distance between axes z and z'.
% Since we are turning about an edge, d = length/2, 
% so mass*d^2 = mass*length^2/4
% Inertia_end = 1/12*mass*(length^2 + width^2) + 1/4*mass*(length^2)
% Inertia_end = 1/4*mass*(length^2+ 1/3*length^2 + 1/3*width^2)
% Inertia_end = 1/4*mass*(4/3*length^2 + 1/3*width^2)

%d/dt  MagnetOrientation = MagnetOrientationVelocity
%d/dt MagnetOrientationVelocity = n*mu*beta*sin(MagOrientation - MagnetOrientation) -
%
%  Aaron Becker, December 2022

T = 0:0.00005:0.6;  % simulation time in seconds.
S = [0 0];  %initial state: [angular_position, angular_velocity]
G = [pi/2 0];  %goal state [angle (rad), angularVelocity (rad/s)]: 90 deg, no velocity.
numCubes = 1;
% controls = {['critPD' ...  '']};
controls = {'constant','ramp','approxBangBang','critPD','highGainPD'};
for j = 1:numel(controls)
    utype = controls{j};
    [t, y] = ode45(@(t,y) odefunMagnetCube(t,y,numCubes,G,utype), T, S);

    % plot the results
    figure(j); clf
    plot(t,y.*[180/pi,1],'linewidth',1.5)
    ylabel('Orientation / Ang velocity [Deg, Rad/s]')
    hold on
    us = zeros(size(t));
    for i = 1:numel(t)
        us(i) = setControl(y(i,:),G(1),t(i),utype);
    end
    % plot the Goal
    plot(t,G(1)*ones(size(t))*180/pi,'b-.','linewidth',1.5)
    % plot the Control
    plot(t,us*180/pi,'r--','linewidth',1.5)
    legend({'Position', 'Speed','goal','control'},'location','best');
    xlabel('Time [s]')
    title(['pivoting magnetic cube, Control = ',utype]);
    grid on
end
    function u= setControl(y,goalAng,t,utype)
        if strcmp(utype, 'constant')
            u = constControl(y,goalAng,t);
        elseif strcmp(utype, 'ramp')
            u = rampControl(y,goalAng,t);
        elseif strcmp(utype, 'approxBangBang')
            u = approxBangBangControl(y,goalAng,t);
        elseif strcmp(utype, 'critPD')
            u = critPDControl(y,goalAng,t);
        elseif strcmp(utype, 'highGainPD')
            u = highGainPDControl(y,goalAng,t);
        end
    end

    function outAng = ClipPlusMinusHalfPi(curang, inAng)
       outAng = max( min(inAng,curang+pi/2 ),curang-pi/2);
    end

function u = highGainPDControl(y,goalAng,t)
        ang = y(1);
        Kp = 50;
        Kd = 0.44;   
       
        propElement = Kp*(goalAng-ang);
        %feedforward term + clipped Kp -  Kd
        u = ClipPlusMinusHalfPi(ang, goalAng + propElement- Kd*y(2)); % + ClipPlusMinusHalfPi(ang,propElement) - Kd*y(2)  ;
       
    end


    function u = critPDControl(y,goalAng,t)
        ang = y(1);
        Kp = 10;
        Kd = 0.12;   
        %For Kp =2, Kd 0.055 is slightly underdamped. 0.057 is overdamped
        %For Kp =1, Kd 0.01 is underdamped. 0.04 is slightly underdamped. 0.05 is overdamped
        propElement = Kp*(goalAng-ang);
        %feedforward term + clipped Kp -  Kd
        u = ClipPlusMinusHalfPi(ang, goalAng + propElement- Kd*y(2)); % + ClipPlusMinusHalfPi(ang,propElement) - Kd*y(2)  ;
       
    end


    function u = approxBangBangControl(y,goalAng,t)
        ang = y(1);
        if t > 0.054         % critical time (stop applying bang bang)
            u = goalAng;           %                 overshoot  ans    undershoot
        elseif ang < goalAng-0.497  %critical angle   [0.045,0.48 0.495,0.497,0.4972 ans,0.4975,0.498 , 0.05]
            u = ang+pi/2;
        else
            u = ang-pi/2;
        end
    end


    function u = constControl(y,goalAng,t)
        u = goalAng;
    end

    function u = rampControl(y,goalAng,t)
        finalTime = 0.25;
        if t<finalTime
            u = t/finalTime*goalAng;
        else
            u = goalAng;
        end
    end


    function dydt = odefunMagnetCube(t,y,numCubes,G, utype)
        % Ordinary Differential Equation function for a cube-chain of
        % length numCubes, with control type utype at time t, and goal
        % angle G.
        %y = [angular_position, angular_velocity]
        length = 0.01; % meters = 10 millimeter  (cube length)
        width = 0.01; %  meters = 10 millimeter   (cube width)
        mubeta = 1; %strength of magnetic field * strength of cube dipole
        mass = 10; %grams
        Inertia = 1/4*mass*(4/3*(numCubes*length)^2 + 1/3*width^2) ;
        b = 0.01; %friction
        u = setControl(y,G(1),t,utype);
        angAcc = 1/Inertia*(  numCubes*mubeta*sin(u - y(1)) - b*y(2)  );
        dydt = [y(2); angAcc];
    end


end