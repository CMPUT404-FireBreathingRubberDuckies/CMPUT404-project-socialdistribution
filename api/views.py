import uuid
from django.core.urlresolvers import reverse
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponseRedirect, HttpResponse
from socialp2p.models import Author, FriendRequest
from socialp2p import views
from api.serializations import AuthorSerializer, FriendRequestSerializer
from django.contrib.auth.models import User
from rest_framework import viewsets, status

class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

@api_view(['GET', 'POST'])
def author_list(request):
    if request.method == 'GET':
        authors = Author.objects.all()
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

    # elif request.method == 'POST':
    #     serializer = AuthorSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def author_detail(request, author_uuid):
    try:
        author_uuid = uuid.UUID(author_uuid)
    except Exception as e:
        return Response(status=status.HTTP_404_NOT_FOUND)

    try:
        author = Author.objects.get(uuid=author_uuid)
    except Author.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AuthorSerializer(author)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = AuthorSerializer(author, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
def friend_request(request, author_uuid):
    author = Author.objects.get(uuid=author_uuid)
    user = User.objects.get(author=author)
    if request.method == 'GET':
	requests = FriendRequest.objects.filter(requester=request.user)
        serializer = FriendRequestSerializer(requests, many=True)
        return Response(serializer.data)
    elif request.method =='POST':
	if FriendRequest.objects.filter(requester=request.user, receiver=user).exists():
		return HttpResponse("Already added Friend")
	else:
		friendRequest = FriendRequest(requester=request.user, receiver=user)
		friendRequest.save()
		#serializer = FriendRequestSerializer(friendRequest)
		return HttpResponseRedirect(reverse('socialp2p:profile', args=[user.username]))
    elif request.method == 'DELETE':
	request = FriendRequest.objects.get(requester=request.user, receiver=user)
	request.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)
