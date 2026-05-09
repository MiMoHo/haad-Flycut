//
//  FlycutImageStore.m
//  Flycut
//
//  File-based image storage for clipboard image clippings.
//

#import "FlycutImageStore.h"

static FlycutImageStore *sharedInstance = nil;

@implementation FlycutImageStore

+(FlycutImageStore *)sharedStore
{
    if (nil == sharedInstance) {
        sharedInstance = [[FlycutImageStore alloc] init];
    }
    return sharedInstance;
}

-(id)init
{
    self = [super init];
    if (self) {
        NSArray *paths = NSSearchPathForDirectoriesInDomains(NSApplicationSupportDirectory, NSUserDomainMask, YES);
        NSString *appSupportDir = [paths firstObject];
        imagesDirectoryPath = [[appSupportDir stringByAppendingPathComponent:@"Flycut/Images"] retain];

        NSFileManager *fm = [NSFileManager defaultManager];
        if (![fm fileExistsAtPath:imagesDirectoryPath]) {
            [fm createDirectoryAtPath:imagesDirectoryPath
          withIntermediateDirectories:YES
                           attributes:nil
                                error:nil];
        }
    }
    return self;
}

-(NSString *)hashForData:(NSData *)data
{
    if (!data || [data length] == 0)
        return nil;

    unsigned char hash[CC_SHA256_DIGEST_LENGTH];
    CC_SHA256([data bytes], (CC_LONG)[data length], hash);
    NSMutableString *hashString = [NSMutableString stringWithCapacity:CC_SHA256_DIGEST_LENGTH * 2];
    for (int i = 0; i < CC_SHA256_DIGEST_LENGTH; i++)
        [hashString appendFormat:@"%02x", hash[i]];
    return hashString;
}

-(NSString *)filePathForHash:(NSString *)hash
{
    return [imagesDirectoryPath stringByAppendingPathComponent:
            [NSString stringWithFormat:@"%@.tiff", hash]];
}

-(BOOL)saveImageData:(NSData *)data forHash:(NSString *)hash
{
    if (!data || !hash)
        return NO;

    NSString *filePath = [self filePathForHash:hash];
    if ([[NSFileManager defaultManager] fileExistsAtPath:filePath])
        return YES;

    return [data writeToFile:filePath atomically:YES];
}

-(NSData *)imageDataForHash:(NSString *)hash
{
    if (!hash)
        return nil;

    NSString *filePath = [self filePathForHash:hash];
    if (![[NSFileManager defaultManager] fileExistsAtPath:filePath])
        return nil;

    return [NSData dataWithContentsOfFile:filePath];
}

-(void)deleteImageForHash:(NSString *)hash
{
    if (!hash)
        return;

    NSString *filePath = [self filePathForHash:hash];
    [[NSFileManager defaultManager] removeItemAtPath:filePath error:nil];
}

-(BOOL)hasImageForHash:(NSString *)hash
{
    if (!hash)
        return NO;

    return [[NSFileManager defaultManager] fileExistsAtPath:[self filePathForHash:hash]];
}

-(NSString *)imagesDirectoryPath
{
    return imagesDirectoryPath;
}

-(NSArray *)allStoredHashes
{
    NSArray *files = [[NSFileManager defaultManager] contentsOfDirectoryAtPath:imagesDirectoryPath error:nil];
    NSMutableArray *hashes = [NSMutableArray arrayWithCapacity:[files count]];
    for (NSString *file in files) {
        if ([file hasSuffix:@".tiff"]) {
            [hashes addObject:[file stringByDeletingPathExtension]];
        }
    }
    return hashes;
}

-(void)dealloc
{
    [imagesDirectoryPath release];
    [super dealloc];
}

@end
