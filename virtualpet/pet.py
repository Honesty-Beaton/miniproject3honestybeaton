from getpass import getuser

from datetime import datetime

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from virtualpet.auth import login_required
from virtualpet.db import get_db

bp = Blueprint('pet', __name__)

def addPet(name, petType, userID):
    db = get_db()
    db.execute(
        'INSERT INTO pet (name, type, userID) VALUES (?, ?, ?)',
        (name, petType, userID)
    )
    db.commit()

def petAction(actionType, petID, userID):
    db = get_db()
    db.execute(
        'INSERT INTO petAction (actionType, petID, userID) VALUES (?, ?, ?)',
        (actionType, petID, userID)
    )
    db.commit()

def getUserPets(userID):
    db = get_db()
    pets = db.execute(
        'SELECT * FROM pet WHERE userID=?',
        (userID,)
    ).fetchall()
    print(f"retrieved pets for user {userID}: {pets}")
    return pets

def getPetByID(petID):
    db = get_db()
    pet = db.execute('SELECT * FROM pet WHERE id = ?', (petID,)).fetchone()

    if pet is not None:
        return dict(pet)
    return None

def getPetStatus(pet):
    hunger = pet['hungerLevel']
    happiness = pet['happinessLevel']
    energy = pet['energyLevel']

    if hunger < 30 or happiness < 30 or energy < 30:
        return "Sad"
    elif 31 <= hunger <= 50 and 31 <= happiness <= 50 and 31 <= energy <= 50:
        return "Average"
    else:
        return "Happy"

def updatePetStatus(pet_id):
    db = get_db()
    pet = db.execute('SELECT * FROM pet WHERE id=?', (pet_id,)).fetchone()

    if pet is not None:
        hunger = pet['hungerLevel']
        happiness = pet['happinessLevel']
        energy = pet['energyLevel']

        # Determine the pet's status based on the levels
        if hunger < 30 or happiness < 30 or energy < 30:
            status = 'Sad'
        elif 31 <= hunger <= 50 and 31 <= happiness <= 50 and 31 <= energy <= 50:
            status = 'Average'
        else:
            status = 'Happy'

        # Update the pet's status in the database
        db.execute('UPDATE pet SET status=?, lastInteraction=CURRENT_TIMESTAMP WHERE id=?', (status, pet_id))
        db.commit()



@bp.route('/')
@login_required
def index():
    pets = getUserPets(g.user['id'])
    currentTime = datetime.now()

    for pet in pets:
        petDict = dict(pet)
        petDict['status'] = getPetStatus(petDict)

    return render_template('pets/index.html', pets = pets, now=currentTime)


@bp.route('/adopt', methods=['GET', 'POST'])
@login_required
def adopt():
    if request.method == 'POST':
        pet_name = request.form['name']
        pet_type = request.form['type']
        user_id = g.user['id']

        try:
            addPet(pet_name, pet_type, user_id)
            flash(f'Successfully adopted {pet_name} the {pet_type}')
            return redirect(url_for('pet.index'))
        except Exception as e:
            flash(f'Error adopting pet: {str(e)}')

    return render_template('pets/adopt.html')

@bp.route('/<int:pet_id>/action', methods=('POST',))
@login_required
def action(pet_id):
    action_type = request.form['action_type']

    db = get_db()
    pet = db.execute('SELECT * FROM pet WHERE id=?', (pet_id,)).fetchone()

    if action_type == 'feed':
        newHunger = min(pet['hungerLevel'] + 10, 100)
        db.execute('UPDATE pet SET hungerLevel=?, lastInteraction=CURRENT_TIMESTAMP WHERE id=?',
                   (newHunger, pet_id))
    elif action_type == 'play':
        new_happiness = min(pet['happinessLevel'] + 10, 100)
        new_hunger = max(pet['hungerLevel'] - 15, 0)
        new_energy = max(pet['energyLevel'] - 10, 0)
        db.execute('UPDATE pet SET happinessLevel=?, hungerLevel=?, energyLevel=?, lastInteraction=CURRENT_TIMESTAMP WHERE id=?',
                   (new_happiness, new_hunger, new_energy, pet_id))

    updatePetStatus(pet_id)
    petAction(action_type, pet_id, g.user['id'])

    flash(f'Performed {action_type} with pet {pet_id}')

    return redirect(url_for('index'))


@bp.route('/<int:pet_id>/nap', methods=('POST',))
@login_required
def nap(pet_id):
    db = get_db()
    pet = db.execute('SELECT * FROM pet WHERE id=?', (pet_id,)).fetchone()

    # Increase energy by a set amount, e.g., 20, but cap it at 100
    new_energy = min(pet['energyLevel'] + 20, 100)

    # Update the pet's energy level and record the last interaction
    db.execute('UPDATE pet SET energyLevel=?, lastInteraction=CURRENT_TIMESTAMP WHERE id=?',
               (new_energy, pet_id))
    updatePetStatus(pet_id)
    db.commit()

    # Flash a message and redirect back to the index
    flash(f'{pet["name"]} took a nap and regained energy!')
    return redirect(url_for('pet.index'))

@bp.route('/<int:pet_id>/status', methods=('POST',))
def getPetStatusByID(pet_id):
    db = get_db()
    pet = db.execute('SELECT * FROM pet WHERE id=?', (pet_id,)).fetchone()

    status = getPetStatus(pet)
    return {'id': pet_id, 'status': status}

@bp.route('/<int:pet_id>/update', methods=('POST',))
@login_required
def updatePet(pet_id):
    new_name = request.form['new_name']
    db = get_db()

    # Update the pet's name in the database
    db.execute('UPDATE pet SET name=?, lastInteraction=CURRENT_TIMESTAMP WHERE id=?',
               (new_name, pet_id))
    db.commit()

    flash(f'Successfully updated the pet\'s name to {new_name}')
    return redirect(url_for('pet.index'))


@bp.route('/<int:pet_id>/delete', methods=['POST'])
@login_required
def delete_pet(pet_id):
    db = get_db()

    # Delete the pet from the database
    db.execute('DELETE FROM pet WHERE id=?', (pet_id,))
    db.commit()

    flash('Pet deleted successfully')
    return redirect(url_for('pet.index'))