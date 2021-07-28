# -----------------------------------------------------------------------------
# Ballon-shooting challenge
# Challenge Specification: 
# https://drive.google.com/file/d/1kE2_qeQNEZO09GSQSD_cLED-yy8GoCa0/view?usp=sharing
# 
# Language - Python
# Modules - pygame (ver 2.0.1), configparser, random
# Controls - Arrow Keys(UP&DOWN)
# 
# -----------------------------------------------------------------------------

"""
Challenge solution:
Step0: define game logic(rules)
    -Game goal: shoot down all balloons on screen
    -player can control a cannon to fire bullets 
    -A bullet can destory one ballon
    -Missed shots will be recorded

Step1: define objects (pygame.sprite for visible game objs)
    -Ballon
    -Cannon
    -Bullet
    TODO: to enrich palybility, add power items, platforms, more mobs

Step2: define actions
    -Ballon's vertical moments are random 
    -Cannon can move up & down with player's control
    -Press "space bar" to fire bullet
    -single tap: one shot, hold "space bar": mulitple bullets.   
        -TODO: after holding the key, cannon can't fire while moving
    -Bullets travel 10 times speed faster to ballon

Step3: draw game UI 
    -Choose object icons(bullet, Ballon, Cannon, background)
    -Game Start Icon
    -Game End Icon
    -Pause & Resume?

Step4: Adding game effects 
    -Object Collisons (AABB? Circular Bounding Box Or Pixel perfect)
    -Sound Effects(Shooting, hit target, game music?)
    -exploation & firing effect?

Step5: Some Adds on
    -configeration file
    -ReadMe

Appendix: 
pyGame game loop:
    while True:
        events() #proceeds events like user inputs
        loop()   #computes changes in the game world
        render() #print out game screen

pyGame toturial: 
    -https://github.com/kidscancode/pygame_tutorials

filesystem path with pathlib
    -https://docs.python.org/3/library/pathlib.html 

manage arguments with configuration file
    -https://docs.python.org/3/library/configparser.html

Sprite Collisions tutorial
    -https://www.youtube.com/watch?v=Dspz3kaTKUg

Problems unsloved:
1.Why in INI file capitalized letter in variables name will convert to small case when accessing it
    -guess: somthing happened during converting INI file into local dict, function called configparser.item()
2.how to meet both single shoot(one tap) & continous shoot(hold) requirement without adding extra function keys
    -current attempt: enable key_repeat, but this does not allow auto shooting while change direction
3.Better way to load img & music without call all each item
    -guess: spritesheet for img, ? for music
4.how to dynamic render text using relative distance.
    -guess: when calucating required distance to display, consider font size as well
5.Is there an easy way to store & acess color settings(stored in tuples) in INI file
"""


import pygame, random, configparser
#for convinent, put some color here
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
WHITE = (255,255,255)

#----------------Game objects
class Ballon(pygame.sprite.Sprite):
    #behaviour dictionary, shows the coefficient relation with coordinate system
    direction = {"stay": 0, "up": -1, "down": 1}

    def __init__(self, game):
        self._layer = int(game.config['LAYER']['ballon_layer'])
        self.groups = game.all_sprites, game.ballons
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.image = game.img_ballon
        self.rect = self.image.get_rect()
        #Ballon randommly spawn on left-side of the screen
        self.half_edge = self.rect.width/2
        self.rect.center = (random.randint(self.half_edge, game.width/2-self.half_edge)
            , random.randint(self.half_edge, game.hight-self.half_edge))
        #initial ballon beheaviour
        self.stay = True
        self.goal = self.rect.centery
        self.destory = False
        self.remaining_time = int(game.config['CONTROL']['ballon_destory_time'])
        self.time = pygame.time.get_ticks()

    def update(self, game):
        
        #not instant kill object
        if self.destory:
            self.remaining_time -= 1
            if self.remaining_time <0:
                self.kill()
        else:
            #don't move during explosion
            self.move()
        #use image mask for perfect collide check
        self.mask = pygame.mask.from_surface(self.image)

    def move(self):
        #take a break after reaching goal
        current_time = pygame.time.get_ticks()
        if self.stay and current_time - self.time > int(game.config['CONTROL']['ballon_stay_time']):
            self.stay = False
            self.time = current_time

        if self.rect.centery == self.goal and not self.stay:
            #randomly decide next place to go(vertical moment)
            self.goal = random.randint(self.half_edge, int(game.config['APP']['window_hight'])-self.half_edge)
            #if next goal happen to be current position
            if self.rect.centery == self.goal: 
                self.stay = True
        elif self.rect.centery > self.goal :
            #ballon below the goal
            self.rect.centery += self.direction['up'] * int(game.config['CONTROL']['basic_speed'])
        elif self.rect.centery < self.goal:
            #above the goal
            self.rect.centery += self.direction['down'] * int(game.config['CONTROL']['basic_speed'])
        #if at the point and in break time, do nothing

    #TODO: add destory animation
    def explosion(self, game):
        #show explosion image
        self.destory = True
        self.image = game.img_explosion
        #add sound effect
        pygame.mixer.Sound.play(game.sound_hit)




class Cannon(pygame.sprite.Sprite):

    def __init__(self, game):
        self._layer = int(game.config['LAYER']['cannon_layer'])
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.image = game.img_cannon
        self.rect = self.image.get_rect()
        #Cannon spawn at right bottom corner of the screen
        self.half_edge = self.rect.width/2
        self.rect.center = (game.width-self.half_edge, game.hight-self.half_edge)
        #tag for auto fire function
        self.auto_fire = False

    def update(self, game):
        keys = pygame.key.get_pressed()
        #player can control cannon moving up & down
        move_distance = int(game.config['CONTROL']['basic_speed'])* int(game.config['CONTROL']['cannon_speed_ratio'])
        if keys[pygame.K_UP] and self.rect.centery > self.half_edge:
            self.rect.centery -= move_distance
        if keys[pygame.K_DOWN] and self.rect.centery < int(game.config['APP']['window_hight'])-self.half_edge:
            self.rect.centery += move_distance
        #check for auto fire
        if self.auto_fire:
            self.fire(game)
    
    #Not used, currently use key_repeat as alternative
    def auto_fire(self, multishoot=False):
        self.auto_fire = multishoot

    def fire(self, game):
        Bullet(game)


        

        

class Bullet(pygame.sprite.Sprite):

    def __init__(self, game):
        self._layer = int(game.config['LAYER']['bullet_layer'])
        self.groups = game.all_sprites, game.bullets
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.image = game.img_bullet
        self.rect = self.image.get_rect()
        #Bullet fire from Cannon
        pygame.mixer.Sound.play(game.sound_fire)
        self.rect.center = game.player.rect.center


    def update(self, game):
        #bullet flying forward at 10 times speed of ballon
        self.rect.centerx -= int(game.config['CONTROL']['bullet_speed_ratio'])*int(game.config['CONTROL']['basic_speed'])
        #if the bullet hit flying outside the window, call it miss
        if self.rect.centerx < 0:
            game.missed += 1
            self.kill()
        self.mask = pygame.mask.from_surface(self.image)



class Game:
#define the game class for better wraping 
    def __init__(self, configeration):
        #load game configerations
        self.loadData(configeration)
        #setting up game window
        pygame.init()       #for the game window
        self.width = int(self.config['APP']['window_width'])
        self.hight = int(self.config['APP']['window_hight'])
        self.screen = pygame.display.set_mode((self.width, self.hight))
        #load image
        self.loadImage()
        #some game attributes
        pygame.display.set_caption(self.config['APP']['title'])
        pygame.display.set_icon(self.img_bullet)
        self.clock = pygame.time.Clock()
        self.running = True
        #load sound effects
        self.loadSound()
       

        



  
    def loadData(self, configeration):
        #load file data into a local dictionary, avoid multiple file access
        parser = configparser.ConfigParser()
        parser.read(configeration)
        self.config = {section: dict(parser.items(section)) for section in parser.sections()} 

    def loadImage(self):
        self.img_ballon = pygame.image.load(self.config['SPRITE']['ballon']).convert_alpha()
        self.img_cannon = pygame.image.load(self.config['SPRITE']['cannon']).convert_alpha()
        self.img_bullet = pygame.image.load(self.config['SPRITE']['bullet']).convert_alpha()
        self.img_explosion = pygame.image.load(self.config['SPRITE']['fire_explosion']).convert_alpha()
        self.img_background = pygame.image.load(self.config['SPRITE']['background']).convert_alpha()
        self.img_op = pygame.image.load(self.config['SPRITE']['op']).convert_alpha()
        self.img_ed = pygame.image.load(self.config['SPRITE']['ed']).convert_alpha()
        #resize them 
        self.img_ballon = pygame.transform.scale(self.img_ballon
            , (int(self.config['SPRITE']['ballon_size']), int(self.config['SPRITE']['ballon_size'])))
        self.img_cannon = pygame.transform.scale(self.img_cannon
            , (int(self.config['SPRITE']['cannon_size']), int(self.config['SPRITE']['cannon_size'])))
        self.img_bullet = pygame.transform.scale(self.img_bullet
            , (int(self.config['SPRITE']['bullet_size']), int(self.config['SPRITE']['bullet_size'])))
        self.img_explosion =pygame.transform.scale(self.img_explosion
            , (int(self.config['SPRITE']['ballon_size']), int(self.config['SPRITE']['ballon_size'])))
        self.img_background = pygame.transform.scale(self.img_background
            , (self.width, self.hight))
        self.img_op = pygame.transform.scale(self.img_op
            , (self.width, self.hight))
        self.img_ed = pygame.transform.scale(self.img_ed
            , (self.width, self.hight))

    def loadSound(self):
        pygame.mixer.init()
        self.sound_fire = pygame.mixer.Sound(self.config['MUSIC']['fire_sound'])
        self.sound_hit  = pygame.mixer.Sound(self.config['MUSIC']['hit_target'])
        #these just file, use mixer.music.load to loop 
        self.sound_background = self.config['MUSIC']['game_play']
        self.sound_op = self.config['MUSIC']['op']
        self.sound_ed = self.config['MUSIC']['ed']

    def new(self):
        #reset some game index
        self.score = 0 
        self.missed = 0 
        self.mob_spawn_interval =int(self.config['CONTROL']['ballon_spawn_time']) 
        #create object groups
        self.all_sprites = pygame.sprite.LayeredUpdates()
        #to have one ballon at the beginning
        self.ballons = pygame.sprite.Group()
        Ballon(self)
        self.bullets = pygame.sprite.Group()
        self.player = Cannon(self)
        self.run()

    def run(self):
        self.start_screen()
        #for looping background
        self.bg_i = 0
        pygame.mixer.music.load(self.sound_background)
        pygame.mixer.music.play(-1)
        while self.playing and self.running:
            self.clock.tick(int(self.config['APP']['fps']))
            self.events()
            self.update()
            self.draw()
        #TODO add end section

    def update(self):
        self.all_sprites.update(self)

        #spawn a mob in accerating frequency , every spawn shortern the interval 
        now = pygame.time.get_ticks()
        #TODO: use timer for spawn count down, current have issue.
        time_to_spawn = (now > self.mob_spawn_interval) and (now % self.mob_spawn_interval == 0)
        if now == 0 or time_to_spawn or not self.ballons:
            Ballon(self)
            self.mob_spawn_interval -= int(self.config['CONTROL']['ballon_spawn_reduction'])

        #hit ballon
        for ballon in self.ballons:
            if pygame.sprite.spritecollide(ballon, self.bullets, True, pygame.sprite.collide_mask) and not ballon.destory:
                self.score += int(self.config['CONTROL']['ballon_score'])
                ballon.explosion(self)

    def events(self):
        #allowing triger multiple event when holding a key
        pygame.key.set_repeat(200, 200)
        for event in pygame.event.get():
            #when close window
            if event.type == pygame.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            #TODO: press ESC for pause-mute sound button
            #Question 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
            #TODO: count for the press time interval, turn on multiple fire
            #alternatively add a weapon switch button
            #press space bar to fire one bullet
                    self.player.fire(self)


    def draw(self):
        self.screen.fill(BLACK)
        #to loop the background
        self.screen.blit(self.img_background, (self.bg_i,0))
        self.screen.blit(self.img_background, (self.width + self.bg_i,0))
        if (self.bg_i == -self.width):
            self.screen.blit(self.img_background, (self.width + self.bg_i,0))
            self.bg_i = 0
        self.bg_i -= 1
        self.all_sprites.draw(self.screen)
        #draw scores
        font = pygame.font.SysFont(pygame.font.match_font(self.config['APP']['text_font'])
            , int(self.config['APP']['text_size']))
        score_text = 'Score: '+ str(self.score)
        missed_text = 'Missed: '+ str(self.missed)
        img_score = font.render(score_text, True, BLUE)
        img_missed = font.render(missed_text, True, BLUE)
        #aline score & miss, put them on right top corner
        #TODO: Failed to dynamic adjust the position
        self.screen.blit(img_score, (600,0))
        self.screen.blit(img_missed, (800,0))

        #refresh all changes to game screen
        pygame.display.update()


    #TODO: show start screen
    def start_screen(self):
        #load background & music
        self.screen.fill(BLACK)
        self.screen.blit(self.img_op, (0,0))
        pygame.mixer.music.load(self.sound_op)
        pygame.mixer.music.play(-1)
        #load font
        font1 = pygame.font.SysFont(pygame.font.match_font(self.config['APP']['title_font'])
            , int(self.config['APP']['title_size']))
        font2 = pygame.font.SysFont(pygame.font.match_font(self.config['APP']['subtitle_font'])
            , int(self.config['APP']['subtitle_size']))
        img_title = font1.render('Ballon Shooting!', True, BLACK)
        img_press_start = font2.render('Press SPACE To Start!', True, BLACK)
        self.screen.blit(img_title, (self.width/4, self.hight/5*1))
        self.screen.blit(img_press_start, (self.width/5*1.5, self.hight/5*3))
        self.playing = False
        while not self.playing:
            for event in pygame.event.get():
                #check input
                if event.type == pygame.QUIT:
                    self.running = False
                    self.playing = True
                if event.type == pygame.KEYDOWN:
                    self.playing = True
                    #TODO: transaction animation
            pygame.display.update()
        
        

    #TODO: show pause screen
    #TODO: show end screen


#start game
configFile = 'config.ini'
game = Game(configFile)
while game.running:
    game.new()

pygame.quit()

