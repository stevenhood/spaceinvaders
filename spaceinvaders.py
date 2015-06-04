#! /usr/bin/env python

# Space Invaders
# version 0.1 (17/04/2013)
# Steven Hood

# Python 2.7.3
# Pygame 1.9.1 (release)

import pygame
import sys
import random
from pygame.sprite import Sprite

pygame.init()
random.seed()

window = (winWidth, winHeight) = 640, 480
muted = False

class Bullet(Sprite):
	def __init__(self, (x, y), direction=-15):
		Sprite.__init__(self)
		self.image = pygame.Surface([3, 10])
		self.image.fill(pygame.Color(255, 0, 0, 100))
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		self.rect.move_ip(0, self.direction)

class Enemy(Sprite):
	names = {
		'enemy1': 'images/enemy1.png',
		'enemy2': 'images/enemy2.png',
		'enemy3': 'images/enemy3.png',
		'enemy4': 'images/enemy4.png'
	}

	def __init__(self, (x, y), name, descend=24, direction=5):
		Sprite.__init__(self)
		self.name = name
		self.image = pygame.image.load(Enemy.names[name]).convert()
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.descend = descend
		self.direction = direction
		self.isBoss = (name == 'enemy4')

	def update(self):
		y = 0
		if self.rect.centerx >= (winWidth - 50) or self.rect.centerx <= 50:
			self.direction = -self.direction
			y = self.descend
		self.rect.move_ip(self.direction, y)

class Shield(Sprite):
	shieldImages = {
		6: 'images/shield6.png',
		5: 'images/shield5.png',
		4: 'images/shield4.png',
		3: 'images/shield3.png',
		2: 'images/shield2.png',
		1: 'images/shield1.png',
	}

	def __init__(self, (x, y), health=6):
		Sprite.__init__(self)
		self.image = pygame.image.load(Shield.shieldImages[health]).convert()
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.health = health

	def damage(self):
		self.health -= 1
		if not self.health:
			return False
		self.image = pygame.image.load(Shield.shieldImages[self.health])
		return True

class Ship(Sprite):
	points = {
		'enemy1':  10,
		'enemy2':  20,
		'enemy3':  40,
		'enemy4': 150
	}

	def __init__(self, (x, y)):
		Sprite.__init__(self)
		self.image = pygame.image.load('images/ship.png').convert()
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.bullets = None
		# self.bullets added by Game.__init__

	def update(self):
		pass

	def left(self):
		self.rect.move_ip(-10, 0)

	def right(self):
		self.rect.move_ip(10, 0)

	def fire(self):
		# only one bullet at a time
		if len(self.bullets) < 1:
			self.bullets.add(Bullet(self.rect.center))
			if not muted:
				pygame.mixer.music.load('sounds/shoot.wav')
				pygame.mixer.music.play()

class Score(Sprite):
	def __init__(self):
		Sprite.__init__(self)
		self.score = 0
		self.wave = 1
		self.color = pygame.Color(51, 255, 0, 100)
		self.font = pygame.font.Font('freaky-fonts_cosmic-alien/ca.ttf', 20)
		self.render_text()
		self.rect = self.image.get_rect()
		self.rect.x, self.rect.y = 10, 10

	def render_text(self):
		self.image = self.font.render("Score {0}          Wave {1}".format(self.score, self.wave), True, self.color)

	def increase(self, n):
		self.score += n
		self.render_text()

class Game(object):
	def __init__(self, ship, screen, score, difficulty=1000):
		self.ship = ship
		self.screen = screen
		self.score = score
		self.bullets = pygame.sprite.Group([])
		self.enemies = pygame.sprite.Group([])
		self.ebullets = pygame.sprite.Group([])
		self.shields = pygame.sprite.Group([])
		self.ship.bullets = self.bullets
		self.bossExists = False
		self.difficulty = difficulty
		self.newGame()

	def newGame(self):
		for shield in self.shields:
			self.shields.remove(shield)

		self.genEnemies((51, 50), 10, 'enemy3')
		self.genEnemies((51, 100), 10, 'enemy2')
		self.genEnemies((51, 150), 10, 'enemy2')
		self.genEnemies((51, 200), 10, 'enemy1')
		self.genEnemies((51, 250), 10, 'enemy1')
		# 114, 420
		self.genShields((150, 420), 4)

	def genEnemies(self, (x, y), n, name):
		for i in xrange(0, n):
			self.enemies.add(Enemy((x, y), name))
			# allow 35px of space between enemies
			x += 35

	def genShields(self, (x, y), n):
		for i in xrange(0, n):
			self.shields.add(Shield((x, y)))
			x += 114

	def checkCollisions(self):
		for enemy in self.enemies:

			# If any one of the invaders reaches the bottom, the game ends
			if enemy.rect.centery > winHeight:
				die(self.screen, self.score.score)
				return

			# Enemies fire randomly (probability increase after each wave, see main())
			if random.randint(1, self.difficulty) == 1:
				self.ebullets.add(Bullet(enemy.rect.center, 10))
				# if not muted:
				# 	pygame.mixer.music.load('sounds/shoot.wav')
				# 	pygame.mixer.music.play()

			for bullet in self.bullets:
				# Destroy bullet sprites that have left the top of the screen
				if bullet.rect.centery < 0:
					self.bullets.remove(bullet)
					#print "bullet removed"
					continue

				# If the player has shot an invader, destroy the colliding 
				# bullet and enemy sprites and increase the score
				if bullet.rect.colliderect(enemy.rect):
					self.score.increase(Ship.points[enemy.name])
					# If the killed enemy is a boss/UFO, allow another to be randomly created
					if enemy.isBoss:
						self.bossExists = False
					self.enemies.remove(enemy)
					self.bullets.remove(bullet)
					if not muted:
						pygame.mixer.music.load('sounds/invaderkilled.wav')
						pygame.mixer.music.play()
					#print "enemy killed"
					continue

				# Test bullet collisions with shields
				for shield in self.shields:
					if bullet.rect.colliderect(shield.rect):
						self.bullets.remove(bullet)
						if not shield.damage():
							self.shields.remove(shield)
							#print "shield destroyed"

			for ebullet in self.ebullets:
				# Destroy enemy bullet sprites that have left the bottom of the screen
				if ebullet.rect.centery > winHeight:
					self.ebullets.remove(ebullet)
					#print "ebullet removed"
					continue

				# If the player has been shot by an invader, the game ends
				if ebullet.rect.colliderect(self.ship.rect):
					die(self.screen, self.score.score)
					return

				# Test enemy bullet collisions with shields
				for shield in self.shields:
					if ebullet.rect.colliderect(shield.rect):
						self.ebullets.remove(ebullet)
						if not shield.damage():
							self.shields.remove(shield)

		# UFO is spawned randomly, can have only one instance at a time
		if random.randint(1, 2500) == 1250 and not self.bossExists:
			self.enemies.add(Enemy((51, 40), 'enemy4', 0))
			self.bossExists = True

def die(screen, score):
	font = pygame.font.Font('freaky-fonts_cosmic-alien/ca.ttf', 36)
	green = pygame.Color(51, 255, 0, 100)
	red = pygame.Color(255, 0, 0, 100)

	logo = pygame.image.load('images/logo_gameover.png').convert()
	game_over = font.render("Game Over", True, green)
	final_score = font.render("Final Score:", True, green)
	scoretext = font.render(str(score), True, red)

	screen.blit(logo, (0, 0))
	screen.blit(game_over, (200, 325))
	screen.blit(final_score, (25, 430))
	screen.blit(scoretext, (360, 430))

	pygame.display.flip()
	pygame.time.wait(5000)
	sys.exit(0)

def setMuted():
	global muted
	muted = not muted

def main():
	screen = pygame.display.set_mode(window)
	pygame.display.set_caption("Space Invaders")
	background = pygame.Surface(window)
	background.fill(pygame.Color(0, 0, 0, 100))
	screen.blit(background, (0, 0))

	clock = pygame.time.Clock()
	score = Score()
	ship = Ship((320, 450))
	game = Game(ship, screen, score)
	sprites = pygame.sprite.Group([ship, score])

	key_map = {
		pygame.K_LEFT:   ship.left,
		pygame.K_RIGHT:  ship.right,
		pygame.K_SPACE:  ship.fire,
		pygame.K_m:      setMuted,
		pygame.K_ESCAPE: pygame.QUIT
	}
	pygame.key.set_repeat(1, 50)

	running = True
	# main game loop
	while running:
		clock.tick(30)
		pygame.display.set_caption("Space Invaders :: {0:.2f} fps".format(clock.get_fps()))

		sprites.update()
		game.bullets.update()
		game.enemies.update()
		game.ebullets.update()
		#game.shields.update()

		game.checkCollisions()

		sprites.draw(screen)
		game.bullets.draw(screen)
		game.enemies.draw(screen)
		game.ebullets.draw(screen)
		game.shields.draw(screen)

		pygame.display.flip()

		sprites.clear(screen, background)
		game.bullets.clear(screen, background)
		game.enemies.clear(screen, background)
		game.ebullets.clear(screen, background)
		game.shields.clear(screen, background)

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN and event.key in key_map:
				key_map[event.key]()
				#print event

		# If all invaders have been destroyed, a new wave is instantiated
		if len(game.enemies.sprites()) < 1:
			game.newGame()
			score.wave += 1
			# Increase difficulty by increasing the probability of enemies shooting and UFOs spawning
			if game.difficulty > 50:
				game.difficulty -= 50

if __name__ == '__main__':
	main()
