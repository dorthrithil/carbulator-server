from src.resources import auth_resources, car_resources, community_resources, refuel_resources, tour_resources, \
    payoff_resources, user_resources, hello_world_resources, task_resources, task_instance_resources, \
    geocoding_resources, event_resources, account_settings_resources


def configure_api(api):
    api.add_resource(auth_resources.UserRegistration, '/register')
    api.add_resource(auth_resources.UserLogin, '/login')
    api.add_resource(auth_resources.UserLogoutAccess, '/logout/access')
    api.add_resource(auth_resources.UserLogoutRefresh, '/logout/refresh')
    api.add_resource(auth_resources.TokenRefresh, '/token/refresh')
    api.add_resource(auth_resources.ForgotPassword, '/forgot-password')
    api.add_resource(auth_resources.ResetPassword, '/reset-password')

    api.add_resource(account_settings_resources.GetAccountSettings, '/account/settings')
    api.add_resource(account_settings_resources.UpdateAccountSettings, '/account/settings')

    api.add_resource(user_resources.AllUsers, '/users')
    api.add_resource(user_resources.UserSearch, '/users/search')
    api.add_resource(user_resources.ChangePassword, '/account/change-password')

    api.add_resource(car_resources.SingleCar, '/cars/<int:id>')
    api.add_resource(car_resources.AllCars, '/cars')
    api.add_resource(car_resources.UserCars, '/account/cars')

    api.add_resource(community_resources.SingleCommunity, '/communities/<int:id>')
    api.add_resource(community_resources.AllCommunities, '/communities')
    api.add_resource(community_resources.UserCommunities, '/account/communities')
    api.add_resource(community_resources.SingleCommunityInvitation, '/communities/invitations/<int:community_id>')
    api.add_resource(community_resources.OpenCommunityInvitationsForUser, '/account/invitations')
    api.add_resource(community_resources.AllCommunityInvitations, '/communities/invitations')
    api.add_resource(community_resources.InvitedUsers, '/communities/<int:community_id>/users/invited')
    api.add_resource(community_resources.MarkCommunityAsFavourite, '/communities/<int:community_id>/mark-as-favourite')
    api.add_resource(community_resources.FavouriteCommunity, '/account/communities/favourite')

    api.add_resource(refuel_resources.AllRefuels, '/communities/<int:community_id>/refuels')
    api.add_resource(refuel_resources.SingleRefuel, '/communities/<int:community_id>/refuels/<int:id>')
    api.add_resource(refuel_resources.UserRefuels, '/account/refuels')

    api.add_resource(tour_resources.AllTours, '/communities/<int:community_id>/tours')
    api.add_resource(tour_resources.LatestTour, '/communities/<int:community_id>/tours/latest')
    api.add_resource(tour_resources.FinishTour, '/communities/<int:community_id>/tours/<int:id>/finish')
    api.add_resource(community_resources.CommunityUsers, '/communities/<int:community_id>/users')
    api.add_resource(tour_resources.ForceFinishTour, '/communities/<int:community_id>/tours/<int:id>/force-finish')
    api.add_resource(tour_resources.SingleTour, '/communities/<int:community_id>/tours/<int:id>')
    api.add_resource(tour_resources.CommunityTours, '/communities/<int:community_id>/tours')
    api.add_resource(tour_resources.RunningCommunityTours, '/communities/<int:community_id>/tours/running')
    api.add_resource(tour_resources.UserTours, '/account/tours/')
    api.add_resource(tour_resources.RunningUserTours, '/account/tours/running')

    api.add_resource(payoff_resources.AllPayoffs, '/communities/<int:id>/payoffs')
    api.add_resource(payoff_resources.CommunityDebts, '/communities/<int:id>/debts/open')
    api.add_resource(payoff_resources.UserDebts, '/account/debts/open')
    api.add_resource(payoff_resources.SettleDebt, '/debts/<int:id>/settle')
    api.add_resource(payoff_resources.UnsettleDebt, '/debts/<int:id>/unsettle')

    api.add_resource(payoff_resources.SinglePayoff, '/payoffs/<int:id>')

    api.add_resource(task_resources.CreateTask, '/communities/<int:community_id>/tasks')
    api.add_resource(task_resources.GetCommunityTasks, '/communities/<int:community_id>/tasks')
    api.add_resource(task_resources.UpdateTask, '/tasks/<int:task_id>')
    api.add_resource(task_resources.GetTask, '/tasks/<int:task_id>')
    api.add_resource(task_resources.DeleteTask, '/tasks/<int:task_id>')

    api.add_resource(task_instance_resources.FinishTaskInstances, '/tasks/instances/<int:task_instance_id>/finish')
    api.add_resource(task_instance_resources.GetOpenCommunityTaskInstances,
                     '/communities/<int:community_id>/tasks/instances/open')
    api.add_resource(task_instance_resources.GetOpenAccountTaskInstances, '/account/tasks/instances/open')

    api.add_resource(event_resources.CreateEvent, '/communities/<int:community_id>/events')
    api.add_resource(event_resources.GetEvents,
                     '/communities/<int:community_id>/events/from/<from_datetime>/to/<to_datetime>')
    api.add_resource(event_resources.EditEvent, '/events/<int:event_id>')
    api.add_resource(event_resources.GetEvent, '/events/<int:event_id>')
    api.add_resource(event_resources.DeleteEvent, '/events/<int:event_id>')

    api.add_resource(geocoding_resources.Geocode, '/geocode/<query>')

    api.add_resource(hello_world_resources.HelloWorld, '/hello')
