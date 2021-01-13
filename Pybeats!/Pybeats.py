import pygame
pygame.init()

import os

#WINDOW SETUP
WIDTH = 1280
HEIGHT = int(WIDTH/16*9)
TITLE = "Pybeats Client"
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(TITLE)

#DIRECTORIES
SONGS = "songs"
FONTS = "fonts"
RECEPTORS = "receptors"


#FONTS
ALLFONTS = os.listdir(FONTS)
MAINFONT = os.path.join(FONTS, "mainfont.ttf")

#RECEPTORS
ALLRECEPTORS = os.listdir(RECEPTORS)
DEFAULTRECEPTOR = pygame.image.load(os.path.join(RECEPTORS, "circle.png"))

DEFAULTPACK = [DEFAULTRECEPTOR, DEFAULTRECEPTOR, DEFAULTRECEPTOR, DEFAULTRECEPTOR]

#Linear Interpolation (wife calcs, and other useful stuff)
def lerp(small, big, fraction):
    return small + (big-small) * fraction

#JUDGEMENTS
MARVELLOUS = int(30/2)
PERFECT = int(60/2)
GREAT = int(90/2)
OKAY = int(120/2)
BAD = int(150/2)
JUDGEMENTNAMES = ["MARVELLOUS", "PERFECT", 'GREAT', 'OKAY', 'BAD']
JUDGEMENTS  = [[0,MARVELLOUS], [MARVELLOUS+1,PERFECT], [PERFECT+1, GREAT], [GREAT+1, OKAY], [OKAY+1, BAD]]

#FPS
ERRORINMS = 5
running = True
clock = pygame.time.Clock()

class Song(object):
    def __init__(self, name):
        self.name = name
        self.scrollspeed, self.music, self.notes = self.convert_notes(os.path.join(SONGS, os.path.join(name, "noteguide.txt")))
        self.music = pygame.mixer_music.load(os.path.join(SONGS, os.path.join(name, self.music)))

    def convert_notes(self, filename):
        file = open(filename, 'r')
        lines = file.readlines()
        scrollspeed = None
        music = None
        notes = [list(), list(), list(), list()]
        for pos,line in enumerate(lines):
            line = line.split('\n')[0]
            if pos == 0:
                scrollspeed = int(line)
                continue
            elif pos == 1:
                music = line
                continue
            else:
                instructions = line.split(',')
                laneno = int(instructions[0])
                ypos = int(instructions[1])
                notes[laneno-1].append(ypos)
        return scrollspeed, music, notes

    def play(self):
        pygame.mixer_music.play()




#CREATE LANE
class Lane(object):
    def __init__(self, x, width, receptory, laneno, keybinds, receptorimage, currentscreen):
        self.x = x
        self.width = width
        self.receptory = receptory
        self.laneno = laneno
        self.assignedkey = keybinds[self.laneno-1]
        self.laneimage = pygame.transform.scale(receptorimage[self.laneno-1], (int(width), int(width)))
        self.currentscreen = currentscreen
        self.notes = currentscreen.currentsong.notes[self.laneno-1]
        self.scrollspeed = currentscreen.currentsong.scrollspeed
    
    def logic(self):
        keys = pygame.key.get_pressed()
        print(self.notes)
        for pos,note in enumerate(self.notes):
            self.notes[pos] += self.scrollspeed
        if keys[self.assignedkey]:
            try:
                lowestnote = max(self.notes)
                self.currentscreen.award_judgement(lowestnote, self)
            except ValueError:
                pass

            

    def draw(self):
        keys = pygame.key.get_pressed()
        if keys[self.assignedkey]:
            SCREEN.blit(pygame.transform.scale(self.laneimage, (int(self.width/4*3), int(self.width/4*3))), (self.x, self.receptory))
        else:
            SCREEN.blit(self.laneimage, (self.x, self.receptory))
        #calculate which notes to render
        for pos,note in enumerate(self.notes):
            if self.notes[pos] > 0 and self.notes[pos] < HEIGHT:
                SCREEN.blit(self.laneimage, (self.x, self.notes[pos]))
            elif self.notes[pos] > HEIGHT:
                try:
                    del self.notes[pos]
                    self.currentscreen.currentstats["MISS"] += 1
                    self.currentscreen.notecount += 1
                except ValueError:
                    pass

#CREATE MAIN GAME
class PlayScreen(object):
    def __init__(self, bindings, receptorimages, currentsong):
        self.bindings = bindings
        self.receptorimages = receptorimages
        self.currentsong = currentsong
        self.notecount = 0
        self.currentaccuracy = 0
        self.currentstats = {"MARVELLOUS":0, "PERFECT":0, "GREAT":0, "OKAY":0, "BAD":0, "MISS":0}
        self.currentscore = 0
        self.perfectscore = 0
        self.lanes = []
        for laneno in range(4):
            self.lanes.append(Lane(WIDTH/3+(100*laneno), 75, HEIGHT/10*9, laneno+1, self.bindings, self.receptorimages, self))
        self.currentsong.play()


    def award_judgement(self, y, lane):
        #calculate distance
        distance = abs(y-lane.receptory)
        print(distance)
        #calculate ms
        try:
            ms = (distance/self.currentsong.scrollspeed)*ERRORINMS
        except ZeroDivisionError:
            print("Contact the map author, the map is broken.")
            quit()
        #cross reference judgements
        for pos, judgement in enumerate(JUDGEMENTS):
            name = JUDGEMENTNAMES[pos]
            if ms > judgement[0] and ms < judgement[1]:
                #calculate wife%
                self.currentstats[name] += 1
                self.notecount += 1
                maxscore = len(self.currentstats)-pos
                minscore = len(self.currentstats)-pos-1
                self.currentscore += lerp(minscore, maxscore, (ms-judgement[0])/(judgement[1]-judgement[0]))
                try:
                    lane.notes.remove(y)
                    print("removing note")
                except ValueError:
                    pass





    def logic(self):
        self.maximumscore = self.notecount*(len(JUDGEMENTS)-1)
        try:
            self.currentaccuracy = self.currentscore/self.maximumscore*100
        except ZeroDivisionError:
            self.currentaccuracy = 0
        for lane in self.lanes:
            lane.logic()

    def draw(self):
        #draw lanes
        for lane in self.lanes:
            lane.draw()
        #draw judgements
        for pos, stat in enumerate(self.currentstats):
            font = pygame.font.Font(MAINFONT, 22)
            key = list(self.currentstats.keys())[pos]
            text = key + " X " + str(self.currentstats[stat])
            text = font.render(text, True, (255,255,255))
            SCREEN.blit(text, (WIDTH/4*3, HEIGHT/20*1+(100*pos)))
        font = pygame.font.Font(MAINFONT, 22)
        text = "Accuracy: "+str(self.currentaccuracy)+"%"
        text = font.render(text, True, (255,255,255))
        SCREEN.blit(text, (WIDTH/4*3, HEIGHT/10*9))


testsong = Song("test")
   
screen = PlayScreen([pygame.K_q, pygame.K_w, pygame.K_o, pygame.K_p], DEFAULTPACK, testsong)    


def logic():
    screen.logic()

def draw():
    screen.draw()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    SCREEN.fill((0,0,0))
    draw()
    pygame.display.update()
    logic()
    clock.tick(1/(ERRORINMS/1000))

pygame.quit()
quit()