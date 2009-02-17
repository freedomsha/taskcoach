//
//  TwoWayState.m
//  TaskCoach
//
//  Created by Jérôme Laheurte on 01/02/09.
//  Copyright 2009 __MyCompanyName__. All rights reserved.
//

#import "TwoWayState.h"
#import "TwoWayNewCategoriesState.h"
#import "Database.h"
#import "Statement.h"
#import "Network.h"
#import "SyncViewController.h"
#import "DomainObject.h"

@implementation TwoWayState

+ stateWithNetwork:(Network *)network controller:(SyncViewController *)controller
{
	return [[[TwoWayState alloc] initWithNetwork:network controller:controller] autorelease];
}

- (void)activated
{
	Statement *req;
	
	req = [[Database connection] statementWithSQL:[NSString stringWithFormat:@"SELECT COUNT(*) AS total FROM Category WHERE status=%d", STATUS_NEW]];
	[req execWithTarget:self action:@selector(onNewCategoriesCount:)];
	
	req = [[Database connection] statementWithSQL:[NSString stringWithFormat:@"SELECT COUNT(*) AS total FROM Task WHERE status=%d", STATUS_NEW]];
	[req execWithTarget:self action:@selector(onNewTasksCount:)];
	
	req = [[Database connection] statementWithSQL:[NSString stringWithFormat:@"SELECT COUNT(*) AS total FROM Task WHERE status=%d", STATUS_DELETED]];
	[req execWithTarget:self action:@selector(onDeletedTasksCount:)];
	
	req = [[Database connection] statementWithSQL:[NSString stringWithFormat:@"SELECT COUNT(*) AS total FROM Task WHERE status=%d", STATUS_MODIFIED]];
	[req execWithTarget:self action:@selector(onModifiedTasksCount:)];
	
	[myNetwork appendInteger:newCategoriesCount];
	[myNetwork appendInteger:newTasksCount];
	[myNetwork appendInteger:deletedTasksCount];
	[myNetwork appendInteger:modifiedTasksCount];
	
	myController.state = [TwoWayNewCategoriesState stateWithNetwork:myNetwork controller:myController];
}

- (void)onNewCategoriesCount:(NSDictionary *)dict
{
	newCategoriesCount = [[dict objectForKey:@"total"] intValue];
}

- (void)onNewTasksCount:(NSDictionary *)dict
{
	newTasksCount = [[dict objectForKey:@"total"] intValue];
}

- (void)onDeletedTasksCount:(NSDictionary *)dict
{
	deletedTasksCount = [[dict objectForKey:@"total"] intValue];
}

- (void)onModifiedTasksCount:(NSDictionary *)dict
{
	modifiedTasksCount = [[dict objectForKey:@"total"] intValue];
}

- (void)networkDidConnect:(Network *)network controller:(SyncViewController *)controller
{
	// n/a
}

- (void)network:(Network *)network didGetData:(NSData *)data controller:(SyncViewController *)controller
{
	// n/a
}

@end