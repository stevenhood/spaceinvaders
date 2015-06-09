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

WINDOW_DIMENSIONS = (WINDOW_WIDTH, WINDOW_HEIGHT) = 640, 480

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

	def __init__(self, (x, y), name, descend=24, direction=1):
		Sprite.__init__(self)
		self.name = name
		self.image = pygame.image.load(Enemy.names[name]).convert()
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.descend = descend
		self.direction = direction
		self.is_boss = (name == 'enemy4')

	def update(self):
		y = 0
		if self.rect.centerx >= (WINDOW_WIDTH - 50) or self.rect.centerx <= 50:
			self.direction = -self.direction
			y = self.descend
		self.rect.move_ip(self.direction, y)

class Shield(Sprite):
	shield_images = {
		6: 'images/shield6.png',
		5: 'images/shield5.png',
		4: 'images/shield4.png',
		3: 'images/shield3.png',
		2: 'images/shield2.png',
		1: 'images/shield1.png',
	}

	def __init__(self, (x, y), health=6):
		Sprite.__init__(self)
		self.image = pygame.image.load(Shield.shield_images[health]).convert()
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.health = health

	def damage(self):
		self.health -= 1
		if not self.health:
			return False
		self.image = pygame.image.load(Shield.shield_images[self.health])
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
		# Set/Added by Game.__init__
		self.bullets = None
		self.muted = False

	def left(self):
		self.rect.move_ip(-10, 0)

	def right(self):
		self.rect.move_ip(10, 0)

	def fire(self):
		# only one bullet at a time
		if len(self.bullets) < 1:
			self.bullets.add(Bullet(self.rect.center))
			if not self.muted:
				pygame.mixer.music.load('sounds/shoot.wav')
				pygame.mixer.music.play()

class Text(Sprite):
	def __init__(self, x, y, text):
		Sprite.__init__(self)
		self.text = text
		self.reset_score()
		self.color = pygame.Color(51, 255, 0, 100) # Green
		self.font = pygame.font.Font('freaky-fonts_cosmic-alien/ca.ttf', 20)
		self.render_text()
		self.rect = self.image.get_rect()
		self.rect.x, self.rect.y = x, y

	def reset_score(self):
		self.score = 0

	def render_text(self):
		self.image = self.font.render(self.text.format(self.score), True, self.color)

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

		self.muted = False
		ship.muted = self.muted
		self.ship.bullets = self.bullets
		self.boss_exists = False
		self.difficulty = difficulty
		self.max_ebullets = 1
		self.new_game()

	def clear(self):
		for bullet in self.bullets:
			self.bullets.remove(bullet)
		for enemy in self.enemies:
			self.enemies.remove(enemy)
		for ebullet in self.ebullets:
			self.ebullets.remove(ebullet)
		for shield in self.shields:
			self.shields.remove(shield)

	def new_game(self):
		self.clear()

		self.gen_enemies((51, 50), 10, 'enemy3')
		self.gen_enemies((51, 100), 10, 'enemy2')
		self.gen_enemies((51, 150), 10, 'enemy2')
		self.gen_enemies((51, 200), 10, 'enemy1')
		self.gen_enemies((51, 250), 10, 'enemy1')
		# 114, 420
		self.gen_shields((150, 420), 4)

	def gen_enemies(self, (x, y), n, name):
		for i in range(0, n):
			self.enemies.add(Enemy((x, y), name))
			# allow 35px of space between enemies
			x += 35

	def gen_shields(self, (x, y), n):
		for i in range(0, n):
			self.shields.add(Shield((x, y)))
			x += 114

	def toggle_muted():
		self.muted = not self.muted
		ship.muted = self.muted

	def check_collisions(self):
		self.check_ebullets()
		for enemy in self.enemies:
			self.check_enemy(enemy)
			self.check_bullets(enemy)

	def check_enemy(self, enemy):
		# If any one of the invaders reaches the bottom, the game ends
		if enemy.rect.centery > WINDOW_HEIGHT:
			self.die()
			return

		# Can have at most self.max_ebullets enemy bullets on screen at a time
		# Enemies fire randomly (probability increase after each wave, see main())
		if len(self.ebullets) < self.max_ebullets and random.randint(1, self.difficulty) == 1:
			self.ebullets.add(Bullet(enemy.rect.center, 10))
			# if not self.muted:
			# 	pygame.mixer.music.load('sounds/shoot.wav')
			# 	pygame.mixer.music.play()

	def check_bullets(self, enemy):
		for bullet in self.bullets:
			# Destroy bullet sprites that have left the top of the screen
			if bullet.rect.centery < 0:
				self.bullets.remove(bullet)
				#print 'bullet removed'
				continue

			# If the player has shot an invader, destroy the colliding 
			# bullet and enemy sprites and increase the score
			if bullet.rect.colliderect(enemy.rect):
				self.score.increase(Ship.points[enemy.name])
				# If the killed enemy is a boss/UFO, allow another to be randomly created
				if enemy.is_boss:
					self.boss_exists = False
				self.enemies.remove(enemy)
				self.bullets.remove(bullet)
				if not self.muted:
					pygame.mixer.music.load('sounds/invaderkilled.wav')
					pygame.mixer.music.play()
				#print 'enemy killed'
				continue

			# Test bullet collisions with shields
			for shield in self.shields:
				if bullet.rect.colliderect(shield.rect):
					self.bullets.remove(bullet)
					if not shield.damage():
						self.shields.remove(shield)
						#print 'shield destroyed'

	def check_ebullets(self):
		for ebullet in self.ebullets:
			# Destroy enemy bullet sprites that have left the bottom of the screen
			if ebullet.rect.centery > WINDOW_HEIGHT:
				self.ebullets.remove(ebullet)
				#print 'ebullet removed'
				continue

			# If the player has been shot by an invader, the game ends
			if ebullet.rect.colliderect(self.ship.rect):
				self.die()
				return

			# Test enemy bullet collisions with shields
			for shield in self.shields:
				if ebullet.rect.colliderect(shield.rect):
					self.ebullets.remove(ebullet)
					if not shield.damage():
						self.shields.remove(shield)

	def random_ufo_spawn(self):
		# UFO is spawned randomly, can have only one instance at a time
		if random.randint(1, 2500) == 1250 and not self.boss_exists:
			self.enemies.add(Enemy((51, 40), 'enemy4', 0))
			self.boss_exists = True

	def die(self):
		font = pygame.font.Font('freaky-fonts_cosmic-alien/ca.ttf', 36)
		green = pygame.Color(51, 255, 0, 100)
		red = pygame.Color(255, 0, 0, 100)

		logo = pygame.image.load('images/logo_gameover.png').convert()
		game_over = font.render('Game Over', True, green)
		final_score = font.render('Final Score:', True, green)
		scoretext = font.render(str(self.score.score), True, red)

		self.screen.blit(logo, (0, 0))
		self.screen.blit(game_over, (200, 325))
		self.screen.blit(final_score, (25, 430))
		self.screen.blit(scoretext, (360, 430))

		pygame.display.flip()
		pygame.time.wait(3000)
		sys.exit(0)

def main():
	pygame.display.set_icon(pygame.image.load('images/icon.ico'))
	screen = pygame.display.set_mode(WINDOW_DIMENSIONS)
	pygame.display.set_caption('Space Invaders')
	background = pygame.Surface(WINDOW_DIMENSIONS)
	background.fill(pygame.Color(0, 0, 0, 100))
	screen.blit(background, (0, 0))

	clock = pygame.time.Clock()
	score = Text(10, 10, 'Score {0}')
	wave = Text(WINDOW_WIDTH - 100, 10, 'Wave {0}')
	ship = Ship((320, 450))
	game = Game(ship, screen, score)
	sprites = pygame.sprite.Group([ship, score, wave])

	def end():
		sys.exit(0)

	key_map = {
		pygame.K_LEFT:   ship.left,
		pygame.K_RIGHT:  ship.right,
		pygame.K_SPACE:  ship.fire,
		pygame.K_m:      game.toggle_muted,
		pygame.K_ESCAPE: end
	}
	pygame.key.set_repeat(1, 50)

	running = True
	# main game loop
	while running:
		clock.tick(30)
		pygame.display.set_caption('Space Invaders :: {0:.2f} fps'.format(clock.get_fps()))

		sprites.update()
		game.bullets.update()
		game.enemies.update()
		game.ebullets.update()
		#game.shields.update()

		game.check_collisions()
		game.random_ufo_spawn()

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

		# If all invaders have been destroyed, a new wave is instantiated
		if len(game.enemies.sprites()) < 1:
			game.new_game()
			wave.increase(1)
			# Increase difficulty by increasing the probability of enemies shooting and UFOs spawning
			if game.difficulty > 50:
				game.difficulty -= 50

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN and event.key in key_map:
				key_map[event.key]()
				#print event


if __name__ == '__main__':
	main()
